from django.test import TestCase

from core.ml_baseline import MLForecastBaseline


class MLForecastBaselineTests(TestCase):
    def test_predict_returns_expected_keys(self):
        prices = [100 + i for i in range(20)]
        baseline = MLForecastBaseline(prices)

        result = baseline.predict(horizon_days=5)

        self.assertIn('current_price', result)
        self.assertIn('predicted_high', result)
        self.assertIn('predicted_low', result)
        self.assertIn('confidence', result)
        self.assertEqual(len(result['forecast_points']), 5)
