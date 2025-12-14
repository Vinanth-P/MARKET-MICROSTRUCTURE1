from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Forecast, ForecastPoint
from django.contrib.auth.models import User


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_forecast_api(request):
    """API endpoint to run a forecast"""
    # Similar logic to run_forecast view but return JSON
    return Response({'message': 'Forecast API endpoint'}, status=status.HTTP_200_OK)


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


