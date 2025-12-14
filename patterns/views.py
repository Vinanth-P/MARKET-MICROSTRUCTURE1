from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import DetectedPattern, PatternAlert, PatternHistory
from dashboard.models import Asset, PriceData
from core.pattern_detection import PatternDetector
from core.data_fetchers import CryptoDataFetcher


@login_required
def live(request):
    """Live pattern detection view"""
    # Initialize defaults
    assets = []
    just_now = []
    earlier = []
    
    try:
        # Get assets - convert to list immediately
        assets = list(Asset.objects.all()[:10])
        
        # Get all alerts - get the queryset first, then slice and convert to list
        # This avoids the "Cannot filter a query once a slice has been taken" error
        alerts_queryset = PatternAlert.objects.select_related('asset').order_by('-created_at')
        
        # Get the most recent 20 alerts and convert to list immediately
        recent_alerts = list(alerts_queryset[:20])
        
        # Now we can safely filter the list (not the queryset)
        now_time = timezone.now()
        cutoff_time = now_time - timedelta(minutes=15)
        
        # Filter the list using list comprehension
        just_now = [alert for alert in recent_alerts if alert.created_at >= cutoff_time]
        earlier = [alert for alert in recent_alerts if alert.created_at < cutoff_time][:10]
        
    except Exception as e:
        # Handle any database errors gracefully
        import traceback
        print(f"Error in patterns live view: {e}")
        traceback.print_exc()
    
    context = {
        'assets': assets,
        'just_now_alerts': just_now,
        'earlier_alerts': earlier,
    }
    return render(request, 'patterns/live.html', context)


@login_required
def detect_patterns(request):
    """Run pattern detection for an asset"""
    if request.method == 'POST':
        asset_symbol = request.POST.get('asset')
        timeframe = request.POST.get('timeframe', '1H')
        
        try:
            asset = Asset.objects.get(symbol=asset_symbol)
        except Asset.DoesNotExist:
            return render(request, 'patterns/live.html', {'error': 'Asset not found'})
        
        # Get price data
        symbol_map = {
            'BTC/USD': 'bitcoin',
            'ETH/USD': 'ethereum',
        }
        crypto_symbol = symbol_map.get(asset_symbol, 'bitcoin')
        historical = CryptoDataFetcher.get_historical_data(crypto_symbol, days=30)
        
        if historical:
            prices = [float(p['price']) for p in historical]
            timestamps = [p['timestamp'] for p in historical]
            
            detector = PatternDetector(prices, timestamps)
            detected = detector.detect_all_patterns()
            
            # Create detected patterns
            for pattern_data in detected:
                DetectedPattern.objects.create(
                    pattern_type=pattern_data['type'],
                    asset=asset,
                    timeframe=timeframe,
                    confidence=pattern_data['confidence'],
                    status='active',
                )
                
                # Create alert
                PatternAlert.objects.create(
                    alert_type='pattern',
                    asset=asset,
                    message=f"{pattern_data['type'].replace('_', ' ').title()} pattern detected with {pattern_data['confidence']}% confidence",
                    confidence=pattern_data['confidence'],
                )
    
    return redirect('patterns:live')


@login_required
def history_view(request):
    """Historical pattern analysis view"""
    patterns = DetectedPattern.objects.all().order_by('-detected_at')[:50]
    
    # Calculate statistics
    total_patterns = DetectedPattern.objects.count()
    success_patterns = DetectedPattern.objects.filter(status='success').count()
    failed_patterns = DetectedPattern.objects.filter(status='failed').count()
    active_patterns = DetectedPattern.objects.filter(status='active').count()
    
    accuracy = (success_patterns / total_patterns * 100) if total_patterns > 0 else 0
    
    context = {
        'patterns': patterns,
        'total_patterns': total_patterns,
        'success_patterns': success_patterns,
        'failed_patterns': failed_patterns,
        'active_patterns': active_patterns,
        'accuracy': accuracy,
    }
    return render(request, 'patterns/history.html', context)


@login_required
def config(request):
    """Pattern detection configuration"""
    return render(request, 'patterns/config.html')
