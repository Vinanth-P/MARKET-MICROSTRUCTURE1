from django.db import models
from django.contrib.auth.models import User
from dashboard.models import Asset
from django.utils import timezone




class Forecast(models.Model):
    RISK_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forecasts')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='forecasts')
    prediction_horizon_days = models.IntegerField(default=7)
    risk_tolerance = models.CharField(max_length=10, choices=RISK_LEVELS, default='medium')
    
    current_price = models.DecimalField(max_digits=20, decimal_places=2)
    predicted_high = models.DecimalField(max_digits=20, decimal_places=2)
    predicted_low = models.DecimalField(max_digits=20, decimal_places=2)
    confidence_score = models.IntegerField(default=0, help_text="Confidence percentage (0-100)")
    
    # Indicator toggles
    rsi_divergence = models.BooleanField(default=False)
    macd_crossover = models.BooleanField(default=False)
    sentiment_analysis = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.asset.symbol} Forecast - {self.prediction_horizon_days} days"


class ForecastPoint(models.Model):
    forecast = models.ForeignKey(Forecast, on_delete=models.CASCADE, related_name='points')
    date = models.DateField()
    predicted_price = models.DecimalField(max_digits=20, decimal_places=2)
    confidence_upper = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    confidence_lower = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['date']
        unique_together = ['forecast', 'date']
    
    def __str__(self):
        return f"{self.forecast.asset.symbol} - {self.date}: {self.predicted_price}"


class Pattern(models.Model):
    PATTERN_TYPES = [
        ('bull_flag', 'Bull Flag'),
        ('bear_flag', 'Bear Flag'),
        ('head_shoulders', 'Head & Shoulders'),
        ('double_top', 'Double Top'),
        ('double_bottom', 'Double Bottom'),
        ('ascending_triangle', 'Ascending Triangle'),
        ('descending_triangle', 'Descending Triangle'),
        ('golden_cross', 'Golden Cross'),
        ('death_cross', 'Death Cross'),
        ('doji', 'Doji Star'),
    ]
    
    forecast = models.ForeignKey(Forecast, on_delete=models.CASCADE, related_name='patterns', null=True, blank=True)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='patterns')
    pattern_type = models.CharField(max_length=30, choices=PATTERN_TYPES)
    timeframe = models.CharField(max_length=10, help_text="e.g., 15m, 1H, 4H, 1D")
    match_percentage = models.IntegerField(default=0, help_text="Pattern match percentage (0-100)")
    detected_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-detected_at']
    
    def __str__(self):
        return f"{self.get_pattern_type_display()} - {self.asset.symbol} ({self.match_percentage}%)"


class BacktestRun(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='backtests')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='backtests')
    symbol = models.CharField(max_length=32)
    interval = models.CharField(max_length=8, default='1d')
    short_window = models.IntegerField(default=10)
    long_window = models.IntegerField(default=50)
    initial_capital = models.DecimalField(max_digits=20, decimal_places=2, default=10000)
    commission_pct = models.DecimalField(max_digits=6, decimal_places=4, default=0.001)
    slippage = models.DecimalField(max_digits=6, decimal_places=4, default=0.0005)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='queued')
    metrics = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Backtest {self.symbol} ({self.short_window}/{self.long_window}) by {self.user.username}"


class TradeLog(models.Model):
    backtest = models.ForeignKey(BacktestRun, on_delete=models.CASCADE, related_name='trades')
    timestamp = models.DateTimeField()
    side = models.CharField(max_length=4, choices=[('buy', 'Buy'), ('sell', 'Sell')])
    price = models.DecimalField(max_digits=20, decimal_places=8)
    size = models.DecimalField(max_digits=20, decimal_places=8)
    pnl = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.side.upper()} {self.backtest.symbol} @ {self.price} on {self.timestamp}"


class EquityPoint(models.Model):
    backtest = models.ForeignKey(BacktestRun, on_delete=models.CASCADE, related_name='equity_points')
    timestamp = models.DateTimeField()
    equity = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.backtest.symbol} equity {self.equity} @ {self.timestamp}"
