"""
Better ML forecast using scikit-learn RandomForestRegressor.

This module is optional — if `scikit-learn` is not installed, the class
will raise ImportError when used and callers should fall back to the
lightweight `MLForecastBaseline`.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional

SKLEARN_AVAILABLE = True
try:
    import numpy as np
    from sklearn.ensemble import RandomForestRegressor
except Exception:
    SKLEARN_AVAILABLE = False


class BetterMLForecast:
    """Train a RandomForest on lag features and forecast recursively.

    Notes:
    - Trains on in-memory historical price series; no external persistence.
    - If scikit-learn isn't installed, raises ImportError on instantiation.
    """

    def __init__(self, prices: List[float], timestamps: Optional[List[datetime]] = None, window: int = 10):
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn and numpy are required for BetterMLForecast")

        self.prices = list(prices or [])
        self.timestamps = timestamps or []
        self.window = max(3, int(window))
        self.model = None
        if len(self.prices) >= self.window + 1:
            self._train()

    def _train(self):
        X = []
        y = []
        arr = np.array(self.prices, dtype=float)
        for i in range(self.window, len(arr)):
            X.append(arr[i - self.window:i])
            y.append(arr[i])

        X = np.array(X)
        y = np.array(y)

        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X, y)

    def predict(self, horizon_days: int = 7) -> Dict:
        if not self.model:
            # Not enough data to train; raise to allow caller to fallback
            raise ValueError("Insufficient data to train BetterMLForecast")

        import numpy as np

        last_window = np.array(self.prices[-self.window:], dtype=float)
        preds = []
        upper = []
        lower = []

        for _ in range(horizon_days):
            next_pred = float(self.model.predict(last_window.reshape(1, -1))[0])
            # Use per-estimator predictions to estimate uncertainty
            all_preds = np.array([est.predict(last_window.reshape(1, -1))[0] for est in self.model.estimators_])
            std = float(np.std(all_preds))

            preds.append(next_pred)
            upper.append(next_pred + max(0.01 * next_pred, std))
            lower.append(max(0.0, next_pred - max(0.01 * next_pred, std)))

            # shift window
            last_window = np.roll(last_window, -1)
            last_window[-1] = next_pred

        # Build forecast points
        base_date = (
            self.timestamps[-1].date() if self.timestamps else datetime.now().date()
        )
        points = []
        for i in range(horizon_days):
            date = base_date + timedelta(days=(i + 1))
            price = Decimal(str(preds[i]))
            points.append({
                "date": date,
                "price": price,
                "confidence_upper": Decimal(str(upper[i])),
                "confidence_lower": Decimal(str(lower[i])),
            })

        predicted_price = float(preds[-1]) if preds else float(self.prices[-1])
        predicted_high = predicted_price * 1.02
        predicted_low = predicted_price * 0.98

        confidence = max(50, 90 - int(np.mean(np.abs(np.diff(preds))) * 100))

        return {
            "current_price": Decimal(str(self.prices[-1])),
            "predicted_high": Decimal(str(predicted_high)),
            "predicted_low": Decimal(str(predicted_low)),
            "predicted_price": Decimal(str(predicted_price)),
            "confidence": int(min(95, max(40, confidence))),
            "forecast_points": points,
            "patterns": [],
        }
