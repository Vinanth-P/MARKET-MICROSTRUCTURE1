from django.db import models
from django.contrib.auth.models import User
from dashboard.models import Asset
from forecast.models import Pattern as ForecastPattern


class DetectedPattern(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    pattern_type = models.CharField(max_length=30, choices=ForecastPattern.PATTERN_TYPES)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='detected_patterns')
    timeframe = models.CharField(max_length=10)
    confidence = models.IntegerField(default=0, help_text="Confidence percentage (0-100)")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    detected_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-detected_at']
    
    def __str__(self):
        return f"{self.get_pattern_type_display()} - {self.asset.symbol} ({self.confidence}%)"


class PatternAlert(models.Model):
    ALERT_TYPES = [
        ('pattern', 'Pattern Detected'),
        ('breakout', 'Breakout'),
        ('reversal', 'Reversal'),
        ('rsi', 'RSI Signal'),
        ('volume', 'Volume Spike'),
    ]
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='alerts')
    pattern = models.ForeignKey(DetectedPattern, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    message = models.TextField()
    confidence = models.IntegerField(default=0, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.asset.symbol}"


class PatternHistory(models.Model):
    pattern = models.ForeignKey(DetectedPattern, on_delete=models.CASCADE, related_name='history')
    predicted_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    actual_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    accuracy = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Accuracy percentage")
    timestamp = models.DateTimeField()
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.pattern} - Accuracy: {self.accuracy}%"
