import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class MLForecastBaseline:
    """
    Lightweight regression baseline on log prices.
    Fits a simple linear trend and projects forward; avoids heavy dependencies.
    """

    def __init__(self, prices: List[float], timestamps: Optional[List[datetime]] = None):
        self.prices = prices or []
        self.timestamps = timestamps or []

    def predict(self, horizon_days: int = 7) -> Dict:
        if len(self.prices) < 3:
            return self._default_prediction(horizon_days=horizon_days)

        current_price = float(self.prices[-1])

        # Fit linear regression on log prices to capture compounded growth.
        x = np.arange(len(self.prices))
        y = np.log(np.maximum(self.prices, 1e-9))
        slope, intercept = np.polyfit(x, y, 1)

        # Estimate volatility from residuals to drive confidence/intervals.
        fitted = intercept + slope * x
        residuals = y - fitted
        vol = float(np.std(residuals)) if len(residuals) > 1 else 0.0

        forecast_points = self._generate_forecast_points(
            current_price=current_price,
            slope=slope,
            intercept=intercept,
            vol=vol,
            horizon_days=horizon_days,
        )

        predicted_price = float(forecast_points[-1]["price"])
        predicted_high = predicted_price * (1 + max(0.01, vol))
        predicted_low = predicted_price * (1 - max(0.01, vol))

        confidence = self._calculate_confidence(vol, len(self.prices))

        return {
            "current_price": Decimal(str(current_price)),
            "predicted_high": Decimal(str(predicted_high)),
            "predicted_low": Decimal(str(predicted_low)),
            "predicted_price": Decimal(str(predicted_price)),
            "confidence": confidence,
            "forecast_points": forecast_points,
            "patterns": [],
        }

    def _calculate_confidence(self, vol: float, sample_size: int) -> int:
        # Start with a neutral score and penalize high volatility / low sample size.
        confidence = 70
        confidence -= int(min(20, vol * 50))
        if sample_size < 10:
            confidence -= 10
        elif sample_size > 50:
            confidence += 5
        return min(95, max(40, confidence))

    def _generate_forecast_points(
        self,
        current_price: float,
        slope: float,
        intercept: float,
        vol: float,
        horizon_days: int,
    ) -> List[Dict]:
        points: List[Dict] = []
        start_idx = len(self.prices) - 1
        base_date = (
            self.timestamps[-1].date() if self.timestamps else datetime.now().date()
        )
        for day in range(1, horizon_days + 1):
            idx = start_idx + day
            log_price = intercept + slope * idx
            price = float(np.exp(log_price))
            # Simple uncertainty band driven by volatility proxy.
            upper = price * (1 + max(0.01, vol))
            lower = price * (1 - max(0.01, vol))
            points.append(
                {
                    "date": base_date + timedelta(days=day),
                    "price": Decimal(str(price)),
                    "confidence_upper": Decimal(str(upper)),
                    "confidence_lower": Decimal(str(lower)),
                }
            )
        return points

    def _default_prediction(self, horizon_days: int = 7) -> Dict:
        current_price = float(self.prices[-1]) if self.prices else 1000.0

        # Create simple flat forecast points so frontend has data to plot
        points: List[Dict] = []
        base_date = (
            self.timestamps[-1].date() if self.timestamps else datetime.now().date()
        )
        for day in range(1, horizon_days + 1):
            date = base_date + timedelta(days=day)
            price = current_price
            upper = price * 1.01
            lower = price * 0.99
            points.append(
                {
                    "date": date,
                    "price": Decimal(str(price)),
                    "confidence_upper": Decimal(str(upper)),
                    "confidence_lower": Decimal(str(lower)),
                }
            )

        predicted_price = float(points[-1]["price"]) if points else current_price

        return {
            "current_price": Decimal(str(current_price)),
            "predicted_high": Decimal(str(predicted_price * 1.02)),
            "predicted_low": Decimal(str(predicted_price * 0.98)),
            "predicted_price": Decimal(str(predicted_price)),
            "confidence": 50,
            "forecast_points": points,
            "patterns": [],
        }

