from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .models import MarketIndicator, Signal, MarketSentiment, Asset, PriceData
from core.data_fetchers import DataSyncService


@api_view(['GET'])
def market_overview(request):
    """API endpoint for market overview data"""
    # Sync latest data
    try:
        DataSyncService.sync_market_indicators()
    except:
        pass
    
    indicators = {}
    for indicator_type in ['sp500', 'btc', 'eth', 'ai_accuracy']:
        latest = MarketIndicator.objects.filter(indicator_type=indicator_type).first()
        if latest:
            indicators[indicator_type] = {
                'value': float(latest.value),
                'change_percent': float(latest.change_percent),
                'timestamp': latest.timestamp.isoformat(),
            }
    
    return Response(indicators)


@api_view(['GET'])
def signals(request):
    """API endpoint for trading signals"""
    limit = int(request.GET.get('limit', 10))
    signals = Signal.objects.all()[:limit]
    
    data = []
    for signal in signals:
        data.append({
            'asset': signal.asset,
            'signal_type': signal.signal_type,
            'entry_price': float(signal.entry_price) if signal.entry_price else None,
            'target_price': float(signal.target_price) if signal.target_price else None,
            'confidence': signal.confidence,
            'notes': signal.notes,
            'created_at': signal.created_at.isoformat(),
        })
    
    return Response(data)


@api_view(['GET'])
def sentiment(request):
    """API endpoint for market sentiment"""
    sentiment = MarketSentiment.objects.first()
    if sentiment:
        return Response({
            'score': sentiment.score,
            'level': sentiment.level,
            'timestamp': sentiment.timestamp.isoformat(),
        })
    return Response({'score': 50, 'level': 'neutral'}, status=status.HTTP_200_OK)


@api_view(['GET'])
def price_data(request, symbol):
    """API endpoint for price data"""
    try:
        asset = Asset.objects.get(symbol=symbol)
        hours = int(request.GET.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        
        prices = PriceData.objects.filter(
            asset=asset,
            timestamp__gte=since
        ).order_by('timestamp')
        
        data = [{
            'timestamp': p.timestamp.isoformat(),
            'price': float(p.price),
            'volume': float(p.volume),
        } for p in prices]
        
        return Response(data)
    except Asset.DoesNotExist:
        return Response({'error': 'Asset not found'}, status=status.HTTP_404_NOT_FOUND)


