import numpy as np
from typing import List, Dict, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from .pattern_detection import TechnicalIndicators, PatternDetector


class PredictionEngine:
    """Generate price predictions using technical analysis"""
    
    def __init__(self, prices: List[float], timestamps: List[datetime] = None):
        self.prices = prices
        self.timestamps = timestamps or []
        self.indicators = TechnicalIndicators()
        self.pattern_detector = PatternDetector(prices, timestamps)
    
    def predict(self, horizon_days: int = 7, use_rsi: bool = False, 
                use_macd: bool = False, use_sentiment: bool = False) -> Dict:
        """
        Generate price prediction for given horizon.
        Returns predicted high, low, confidence, and forecast points.
        """
        if len(self.prices) < 10:
            return self._default_prediction()
        
        # Calculate trend
        recent_trend = self._calculate_trend()
        
        # Get current price
        current_price = float(self.prices[-1])
        
        # Base prediction on trend
        if recent_trend > 0.02:  # Strong upward trend
            predicted_change = 0.05 + (recent_trend * 2)
        elif recent_trend > 0:
            predicted_change = 0.02 + recent_trend
        elif recent_trend < -0.02:  # Strong downward trend
            predicted_change = -0.03 + (recent_trend * 1.5)
        else:
            predicted_change = recent_trend
        
        # Adjust based on indicators
        if use_rsi:
            rsi = self.indicators.calculate_rsi(self.prices)
            if rsi > 70:  # Overbought
                predicted_change *= 0.7
            elif rsi < 30:  # Oversold
                predicted_change *= 1.3
        
        if use_macd:
            macd = self.indicators.calculate_macd(self.prices)
            if macd['histogram'] > 0:  # Bullish
                predicted_change *= 1.1
            else:  # Bearish
                predicted_change *= 0.9
        
        # Pattern adjustments
        patterns = self.pattern_detector.detect_all_patterns()
        pattern_adjustment = 1.0
        for pattern in patterns:
            if pattern['type'] == 'bull_flag':
                pattern_adjustment *= 1.15
            elif pattern['type'] == 'golden_cross':
                pattern_adjustment *= 1.1
        
        predicted_change *= pattern_adjustment
        
        # Calculate predicted prices
        predicted_price = current_price * (1 + predicted_change)
        predicted_high = predicted_price * 1.03  # 3% above predicted
        predicted_low = predicted_price * 0.97   # 3% below predicted
        
        # Calculate confidence based on data quality and indicators
        confidence = self._calculate_confidence(use_rsi, use_macd, patterns)
        
        # Generate forecast points
        forecast_points = self._generate_forecast_points(
            current_price, predicted_price, horizon_days
        )
        
        return {
            'current_price': Decimal(str(current_price)),
            'predicted_high': Decimal(str(predicted_high)),
            'predicted_low': Decimal(str(predicted_low)),
            'predicted_price': Decimal(str(predicted_price)),
            'confidence': confidence,
            'forecast_points': forecast_points,
            'patterns': patterns,
        }
    
    def _calculate_trend(self) -> float:
        """Calculate recent price trend"""
        if len(self.prices) < 10:
            return 0.0
        
        recent = self.prices[-10:]
        older = self.prices[-20:-10] if len(self.prices) >= 20 else self.prices[:10]
        
        recent_avg = np.mean(recent)
        older_avg = np.mean(older) if older else recent_avg
        
        if older_avg == 0:
            return 0.0
        
        return (recent_avg - older_avg) / older_avg
    
    def _calculate_confidence(self, use_rsi: bool, use_macd: bool, 
                              patterns: List[Dict]) -> int:
        """Calculate prediction confidence score"""
        base_confidence = 70
        
        # Add confidence for indicators used
        if use_rsi:
            base_confidence += 5
        if use_macd:
            base_confidence += 5
        if patterns:
            base_confidence += min(10, len(patterns) * 3)
        
        # Adjust based on data quality
        if len(self.prices) > 50:
            base_confidence += 5
        elif len(self.prices) < 20:
            base_confidence -= 10
        
        return min(95, max(50, base_confidence))
    
    def _generate_forecast_points(self, current_price: float, 
                                  predicted_price: float, 
                                  horizon_days: int) -> List[Dict]:
        """Generate daily forecast points"""
        points = []
        price_change = predicted_price - current_price
        daily_change = price_change / horizon_days
        
        base_date = datetime.now()
        for day in range(1, horizon_days + 1):
            date = base_date + timedelta(days=day)
            price = current_price + (daily_change * day)
            # Add some variance
            variance = price * 0.02 * np.sin(day * np.pi / horizon_days)
            price += variance
            
            points.append({
                'date': date.date(),
                'price': Decimal(str(price)),
                'confidence_upper': Decimal(str(price * 1.02)),
                'confidence_lower': Decimal(str(price * 0.98)),
            })
        
        return points
    
    def _default_prediction(self) -> Dict:
        """Return default prediction when insufficient data"""
        current_price = float(self.prices[-1]) if self.prices else 1000.0
        return {
            'current_price': Decimal(str(current_price)),
            'predicted_high': Decimal(str(current_price * 1.05)),
            'predicted_low': Decimal(str(current_price * 0.95)),
            'predicted_price': Decimal(str(current_price)),
            'confidence': 50,
            'forecast_points': [],
            'patterns': [],
        }


