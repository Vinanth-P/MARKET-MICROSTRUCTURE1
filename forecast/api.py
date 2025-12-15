from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from dashboard.models import Asset
from core.data_fetchers import CryptoDataFetcher
from core.ml_baseline import MLForecastBaseline
from .models import Forecast, ForecastPoint, Pattern
from django.contrib.auth.models import User
from core.backtester import run_backtest
from .models import BacktestRun, TradeLog, EquityPoint
from django.conf import settings
from decimal import Decimal


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_forecast_api(request):
    """API endpoint to run a forecast"""
    data = request.data
    asset_symbol = data.get('asset')
    horizon_days = int(data.get('horizon', 7))
    risk_tolerance = data.get('risk', 'medium')

    rsi_divergence = bool(data.get('rsi_divergence', False))
    macd_crossover = bool(data.get('macd_crossover', False))
    sentiment_analysis = bool(data.get('sentiment_analysis', False))

    try:
        asset = Asset.objects.get(symbol=asset_symbol)
    except Asset.DoesNotExist:
        return Response({'error': 'Asset not found'}, status=status.HTTP_404_NOT_FOUND)

    symbol_map = {
        'BTC/USD': 'bitcoin',
        'ETH/USD': 'ethereum',
    }
    crypto_symbol = symbol_map.get(asset_symbol, 'bitcoin')

    historical = CryptoDataFetcher.get_historical_data(crypto_symbol, days=30)
    if not historical:
        prices = [float(asset.current_price)]
        timestamps = [timezone.now()]
    else:
        prices = [float(p['price']) for p in historical]
        timestamps = [p['timestamp'] for p in historical]

    baseline = MLForecastBaseline(prices, timestamps)
    prediction = baseline.predict(horizon_days=horizon_days)

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

    for point in prediction['forecast_points']:
        ForecastPoint.objects.create(
            forecast=forecast,
            date=point['date'],
            predicted_price=point['price'],
            confidence_upper=point['confidence_upper'],
            confidence_lower=point['confidence_lower'],
        )

    for pattern_data in prediction['patterns']:
        Pattern.objects.create(
            forecast=forecast,
            asset=asset,
            pattern_type=pattern_data['type'],
            timeframe='1D',
            match_percentage=pattern_data['confidence'],
        )

    response_data = {
        'id': forecast.id,
        'asset': forecast.asset.symbol,
        'current_price': float(forecast.current_price),
        'predicted_high': float(forecast.predicted_high),
        'predicted_low': float(forecast.predicted_low),
        'confidence': forecast.confidence_score,
        'horizon_days': forecast.prediction_horizon_days,
        'points': [
            {
                'date': p.date.isoformat(),
                'price': float(p.predicted_price),
                'upper': float(p.confidence_upper) if p.confidence_upper else None,
                'lower': float(p.confidence_lower) if p.confidence_lower else None,
            }
            for p in forecast.points.all().order_by('date')
        ],
    }

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def forecast_detail(request, forecast_id):
    """Get forecast details"""
    try:
        forecast = Forecast.objects.get(id=forecast_id, user=request.user)
        points = forecast.points.all().order_by('date')
        
        data = {
            'id': forecast.id,
            'asset': forecast.asset.symbol,
            'current_price': float(forecast.current_price),
            'predicted_high': float(forecast.predicted_high),
            'predicted_low': float(forecast.predicted_low),
            'confidence': forecast.confidence_score,
            'horizon_days': forecast.prediction_horizon_days,
            'points': [{
                'date': p.date.isoformat(),
                'price': float(p.predicted_price),
                'upper': float(p.confidence_upper) if p.confidence_upper else None,
                'lower': float(p.confidence_lower) if p.confidence_lower else None,
            } for p in points],
        }
        return Response(data)
    except Forecast.DoesNotExist:
        return Response({'error': 'Forecast not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def forecast_history(request):
    """Get user's forecast history"""
    forecasts = Forecast.objects.filter(user=request.user).order_by('-created_at')
    
    data = [{
        'id': f.id,
        'asset': f.asset.symbol,
        'confidence': f.confidence_score,
        'created_at': f.created_at.isoformat(),
    } for f in forecasts]
    
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_backtest_api(request):
    """Run an SMA backtest + LR prediction; optionally save results."""
    data = request.data
    symbol = data.get('symbol', 'BTCUSDT')
    interval = data.get('interval', '1d')
    short_window = int(data.get('short_window', 10))
    long_window = int(data.get('long_window', 50))
    initial_capital = float(data.get('initial_capital', 10000))
    commission = float(data.get('commission_pct', 0.001))
    slippage = float(data.get('slippage', 0.0005))
    forecast_days = int(data.get('forecast_days', 5))
    save = bool(data.get('save', False))

    # Fetch candles from Binance
    candles = CryptoDataFetcher.get_binance_klines(symbol, interval=interval, limit=500)

    # Fallback: if Binance returned no candles, try CoinGecko historical data for common symbols
    if not candles:
        # Map common symbols to coingecko ids
        symbol_map = {
            'BTCUSDT': 'bitcoin',
            'BTC/USD': 'bitcoin',
            'ETHUSDT': 'ethereum',
            'ETH/USD': 'ethereum',
        }
        cg_id = symbol_map.get(symbol.upper())
        if cg_id:
            historical = CryptoDataFetcher.get_historical_data(cg_id, days=90)
            if historical:
                # convert CoinGecko price points into candle-like dicts
                candles = []
                for p in historical:
                    candles.append({
                        'timestamp': p['timestamp'],
                        'open': float(p['price']),
                        'high': float(p['price']),
                        'low': float(p['price']),
                        'close': float(p['price']),
                        'volume': 0.0,
                    })

    result = run_backtest(candles, short_window=short_window, long_window=long_window,
                          initial_capital=initial_capital, commission_pct=commission,
                          slippage=slippage, forecast_days=forecast_days, interval=interval)

    response_payload = result

    if save:
        # Persist BacktestRun and associated trades/equity points
        try:
            asset = Asset.objects.filter(symbol__icontains=symbol.replace('USDT', '/USD')).first()
        except Exception:
            asset = None

        backtest = BacktestRun.objects.create(
            user=request.user,
            asset=asset if asset else Asset.objects.first(),
            symbol=symbol,
            interval=interval,
            short_window=short_window,
            long_window=long_window,
            initial_capital=Decimal(str(initial_capital)),
            commission_pct=Decimal(str(commission)),
            slippage=Decimal(str(slippage)),
            metrics=result.get('metrics', {}),
        )

        for t in result.get('trades', []):
            TradeLog.objects.create(
                backtest=backtest,
                timestamp=t.get('timestamp'),
                side=(t.get('type') or '').lower(),
                price=Decimal(str(t.get('price'))),
                size=Decimal(str(t.get('size', 0))),
                pnl=Decimal(str(t.get('pnl', 0))) if t.get('pnl') is not None else None,
                note='saved'
            )

        for e in result.get('equity', []):
            EquityPoint.objects.create(
                backtest=backtest,
                timestamp=e.get('timestamp'),
                equity=Decimal(str(e.get('equity'))),
            )

        response_payload['backtest_id'] = backtest.id

    return Response(response_payload, status=status.HTTP_200_OK)


