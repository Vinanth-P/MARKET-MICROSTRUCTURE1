import numpy as np
from typing import List, Dict, Tuple
from decimal import Decimal
from datetime import datetime, timedelta


class TechnicalIndicators:
    """Calculate technical indicators"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        prices_array = np.array(prices)
        ema_fast = TechnicalIndicators._ema(prices_array, fast)
        ema_slow = TechnicalIndicators._ema(prices_array, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators._ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': float(macd_line[-1]) if len(macd_line) > 0 else 0,
            'signal': float(signal_line[-1]) if len(signal_line) > 0 else 0,
            'histogram': float(histogram[-1]) if len(histogram) > 0 else 0,
        }
    
    @staticmethod
    def _ema(data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        alpha = 2 / (period + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        
        return ema
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> float:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return float(np.mean(prices)) if prices else 0.0
        return float(np.mean(prices[-period:]))


class PatternDetector:
    """Detect chart patterns in price data"""
    
    def __init__(self, prices: List[float], timestamps: List[datetime] = None):
        self.prices = prices
        self.timestamps = timestamps or []
    
    def detect_bull_flag(self) -> Dict:
        """Detect Bull Flag pattern"""
        if len(self.prices) < 20:
            return {'detected': False, 'confidence': 0}
        
        # Look for upward trend followed by consolidation
        recent_prices = self.prices[-20:]
        first_half = recent_prices[:10]
        second_half = recent_prices[10:]
        
        # Check for upward trend in first half
        trend_up = np.mean(first_half[-5:]) > np.mean(first_half[:5])
        
        # Check for consolidation in second half (low volatility)
        second_std = np.std(second_half)
        first_std = np.std(first_half)
        consolidation = second_std < first_std * 0.7
        
        if trend_up and consolidation:
            confidence = min(95, 60 + int((1 - second_std / first_std) * 35))
            return {'detected': True, 'confidence': confidence}
        
        return {'detected': False, 'confidence': 0}
    
    def detect_head_shoulders(self) -> Dict:
        """Detect Head & Shoulders pattern"""
        if len(self.prices) < 15:
            return {'detected': False, 'confidence': 0}
        
        # Simplified detection: look for three peaks
        recent = self.prices[-15:]
        peaks = []
        
        for i in range(1, len(recent) - 1):
            if recent[i] > recent[i-1] and recent[i] > recent[i+1]:
                peaks.append((i, recent[i]))
        
        if len(peaks) >= 3:
            # Check if middle peak is highest (head)
            peaks = sorted(peaks, key=lambda x: x[1], reverse=True)
            if len(peaks) >= 3:
                middle_peak = peaks[1]  # Second highest should be in middle
                confidence = 65 + int((middle_peak[1] / peaks[0][1]) * 20)
                return {'detected': True, 'confidence': min(95, confidence)}
        
        return {'detected': False, 'confidence': 0}
    
    def detect_double_bottom(self) -> Dict:
        """Detect Double Bottom pattern"""
        if len(self.prices) < 20:
            return {'detected': False, 'confidence': 0}
        
        recent = self.prices[-20:]
        troughs = []
        
        for i in range(1, len(recent) - 1):
            if recent[i] < recent[i-1] and recent[i] < recent[i+1]:
                troughs.append((i, recent[i]))
        
        if len(troughs) >= 2:
            # Check if two troughs are similar in price
            troughs = sorted(troughs, key=lambda x: x[1])
            if len(troughs) >= 2:
                diff = abs(troughs[0][1] - troughs[1][1]) / troughs[0][1]
                if diff < 0.03:  # Within 3%
                    confidence = 70 + int((1 - diff * 10) * 25)
                    return {'detected': True, 'confidence': min(95, confidence)}
        
        return {'detected': False, 'confidence': 0}
    
    def detect_golden_cross(self, short_period: int = 50, long_period: int = 200) -> Dict:
        """Detect Golden Cross (short MA crosses above long MA)"""
        if len(self.prices) < long_period + 5:
            return {'detected': False, 'confidence': 0}
        
        short_ma = TechnicalIndicators.calculate_sma(self.prices, short_period)
        long_ma = TechnicalIndicators.calculate_sma(self.prices, long_period)
        
        # Previous values for crossover detection
        prev_short = TechnicalIndicators.calculate_sma(self.prices[:-1], short_period) if len(self.prices) > short_period else short_ma
        prev_long = TechnicalIndicators.calculate_sma(self.prices[:-1], long_period) if len(self.prices) > long_period else long_ma
        
        # Check for crossover
        if prev_short <= prev_long and short_ma > long_ma:
            confidence = 75 + int((short_ma / long_ma - 1) * 20)
            return {'detected': True, 'confidence': min(95, confidence)}
        
        return {'detected': False, 'confidence': 0}
    
    def detect_all_patterns(self) -> List[Dict]:
        """Detect all patterns and return results"""
        patterns = []
        
        bull_flag = self.detect_bull_flag()
        if bull_flag['detected']:
            patterns.append({'type': 'bull_flag', 'confidence': bull_flag['confidence']})
        
        head_shoulders = self.detect_head_shoulders()
        if head_shoulders['detected']:
            patterns.append({'type': 'head_shoulders', 'confidence': head_shoulders['confidence']})
        
        double_bottom = self.detect_double_bottom()
        if double_bottom['detected']:
            patterns.append({'type': 'double_bottom', 'confidence': double_bottom['confidence']})
        
        golden_cross = self.detect_golden_cross()
        if golden_cross['detected']:
            patterns.append({'type': 'golden_cross', 'confidence': golden_cross['confidence']})
        
        return patterns


