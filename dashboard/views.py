from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import MarketIndicator, Signal, MarketSentiment, Asset, PriceData
from core.data_fetchers import DataSyncService


@login_required
def overview(request):
    """Main market overview dashboard"""
    # Sync latest data
    try:
        DataSyncService.sync_market_indicators()
        DataSyncService.sync_sentiment()
    except Exception as e:
        print(f"Error syncing data: {e}")
    
    # Get latest indicators
    indicators = {}
    for indicator_type in ['sp500', 'btc', 'eth', 'ai_accuracy']:
        latest = MarketIndicator.objects.filter(indicator_type=indicator_type).first()
        if latest:
            indicators[indicator_type] = latest
    
    # Get latest signals (last 10)
    signals = Signal.objects.all()[:10]
    
    # Get latest sentiment
    sentiment = MarketSentiment.objects.first()
    
    # Get Bitcoin asset for detail view
    btc_asset = Asset.objects.filter(symbol='BTC/USD').first()
    
    context = {
        'indicators': indicators,
        'signals': signals,
        'sentiment': sentiment,
        'btc_asset': btc_asset,
    }
    return render(request, 'dashboard/overview.html', context)


@login_required
def asset_detail(request, symbol):
    """Asset detail view with chart"""
    asset = get_object_or_404(Asset, symbol=symbol)
    
    # Get price data for chart (last 24 hours)
    since = timezone.now() - timedelta(hours=24)
    price_data = PriceData.objects.filter(
        asset=asset,
        timestamp__gte=since
    ).order_by('timestamp')[:100]
    
    # Get latest forecast if exists
    from forecast.models import Forecast
    latest_forecast = Forecast.objects.filter(asset=asset).first()
    
    context = {
        'asset': asset,
        'price_data': price_data,
        'forecast': latest_forecast,
    }
    return render(request, 'dashboard/asset_detail.html', context)
