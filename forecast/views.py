from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Forecast, ForecastPoint, Pattern
from dashboard.models import Asset
from core.data_fetchers import CryptoDataFetcher
from core.ml_baseline import MLForecastBaseline
try:
    from core.better_ml import BetterMLForecast
except Exception:
    BetterMLForecast = None
from datetime import datetime, timedelta


@login_required
def index(request):
    """Forecast configuration and results view"""
    assets = Asset.objects.all()[:10]
    recent_forecasts = Forecast.objects.filter(user=request.user).order_by('-created_at')[:5]
    latest_forecast = recent_forecasts.first() if recent_forecasts else None
    latest_points = latest_forecast.points.all().order_by('date') if latest_forecast else []
    
    context = {
        'assets': assets,
        'recent_forecasts': recent_forecasts,
        'latest_forecast': latest_forecast,
        'latest_points': latest_points,
    }
    return render(request, 'forecast/index.html', context)


@login_required
def run_forecast(request):
    """Run a new forecast"""
    if request.method == 'POST':
        asset_symbol = request.POST.get('asset')
        horizon_days = int(request.POST.get('horizon', 7))
        risk_tolerance = request.POST.get('risk', 'medium')
        
        rsi_divergence = request.POST.get('rsi_divergence') == 'on'
        macd_crossover = request.POST.get('macd_crossover') == 'on'
        sentiment_analysis = request.POST.get('sentiment_analysis') == 'on'
        
        try:
            asset = Asset.objects.get(symbol=asset_symbol)
        except Asset.DoesNotExist:
            messages.error(request, 'Asset not found')
            return redirect('forecast:index')
        
        # Get historical price data
        symbol_map = {
            'BTC/USD': 'bitcoin',
            'ETH/USD': 'ethereum',
        }
        crypto_symbol = symbol_map.get(asset_symbol, 'bitcoin')
        
        # Fetch historical data
        historical = CryptoDataFetcher.get_historical_data(crypto_symbol, days=30)
        
        if not historical:
            # Use current price as fallback
            prices = [float(asset.current_price)]
            timestamps = [timezone.now()]
        else:
            prices = [float(p['price']) for p in historical]
            timestamps = [p['timestamp'] for p in historical]
        
        # Prefer improved ML model if available; fallback to baseline
        prediction = None
        if BetterMLForecast:
            try:
                better = BetterMLForecast(prices, timestamps)
                prediction = better.predict(horizon_days=horizon_days)
            except Exception:
                prediction = None

        if prediction is None:
            baseline = MLForecastBaseline(prices, timestamps)
            prediction = baseline.predict(horizon_days=horizon_days)
        
        # Create forecast
        forecast = Forecast.objects.create(
            user=request.user,
            asset=asset,
            prediction_horizon_days=horizon_days,
            risk_tolerance=risk_tolerance,
            current_price=prediction['current_price'],
            predicted_high=prediction['predicted_high'],
            predicted_low=prediction['predicted_low'],
            confidence_score=prediction['confidence'],
            rsi_divergence=rsi_divergence,
            macd_crossover=macd_crossover,
            sentiment_analysis=sentiment_analysis,
        )
        
        # Create forecast points
        for point in prediction['forecast_points']:
            ForecastPoint.objects.create(
                forecast=forecast,
                date=point['date'],
                predicted_price=point['price'],
                confidence_upper=point['confidence_upper'],
                confidence_lower=point['confidence_lower'],
            )
        
        # Create detected patterns
        for pattern_data in prediction['patterns']:
            Pattern.objects.create(
                forecast=forecast,
                asset=asset,
                pattern_type=pattern_data['type'],
                timeframe='1D',
                match_percentage=pattern_data['confidence'],
            )
        
        messages.success(request, f'Forecast generated successfully!')
        return redirect('forecast:results', forecast_id=forecast.id)
    
    return redirect('forecast:index')


@login_required
def results(request, forecast_id):
    """View forecast results"""
    forecast = get_object_or_404(Forecast, id=forecast_id, user=request.user)
    forecast_points = forecast.points.all().order_by('date')
    patterns = forecast.patterns.all()
    
    context = {
        'forecast': forecast,
        'forecast_points': forecast_points,
        'patterns': patterns,
    }
    return render(request, 'forecast/results.html', context)


@login_required
def history(request):
    """Historical forecast accuracy view"""
    forecasts = Forecast.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'forecasts': forecasts,
    }
    return render(request, 'forecast/history.html', context)
