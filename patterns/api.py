from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import DetectedPattern, PatternAlert
from django.utils import timezone
from datetime import timedelta


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def detect_patterns_api(request):
    """API endpoint to run pattern detection"""
    return Response({'message': 'Pattern detection API endpoint'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def live_alerts(request):
    """Get live pattern alerts"""
    limit = int(request.GET.get('limit', 20))
    alerts = PatternAlert.objects.all().order_by('-created_at')[:limit]
    
    data = [{
        'id': a.id,
        'alert_type': a.alert_type,
        'asset': a.asset.symbol,
        'message': a.message,
        'confidence': a.confidence,
        'created_at': a.created_at.isoformat(),
    } for a in alerts]
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pattern_history_api(request):
    """Get historical pattern data"""
    patterns = DetectedPattern.objects.all().order_by('-detected_at')[:50]
    
    data = [{
        'id': p.id,
        'pattern_type': p.pattern_type,
        'asset': p.asset.symbol,
        'timeframe': p.timeframe,
        'confidence': p.confidence,
        'status': p.status,
        'detected_at': p.detected_at.isoformat(),
    } for p in patterns]
    
    return Response(data)


