from django.db import models
from django.contrib.auth.models import User


class MarketIndicator(models.Model):
    INDICATOR_TYPES = [
        ('sp500', 'S&P 500'),
        ('btc', 'BTC/USD'),
        ('eth', 'ETH/USD'),
        ('ai_accuracy', 'AI Accuracy'),
    ]
    
    indicator_type = models.CharField(max_length=20, choices=INDICATOR_TYPES)
    value = models.DecimalField(max_digits=20, decimal_places=2)
    change_percent = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['indicator_type', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_indicator_type_display()}: {self.value} ({self.change_percent}%)"


class Signal(models.Model):
    SIGNAL_TYPES = [
        ('LONG', 'Long'),
        ('SHORT', 'Short'),
        ('NEUTRAL', 'Neutral'),
    ]
    
    asset = models.CharField(max_length=20)
    signal_type = models.CharField(max_length=10, choices=SIGNAL_TYPES)
    entry_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    target_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    confidence = models.IntegerField(default=0, help_text="Confidence percentage (0-100)")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.asset} {self.signal_type} - {self.confidence}%"


class MarketSentiment(models.Model):
    SENTIMENT_LEVELS = [
        ('extreme_fear', 'Extreme Fear'),
        ('fear', 'Fear'),
        ('neutral', 'Neutral'),
        ('greed', 'Greed'),
        ('extreme_greed', 'Extreme Greed'),
    ]
    
    score = models.IntegerField(default=50, help_text="Sentiment score (0-100)")
    level = models.CharField(max_length=20, choices=SENTIMENT_LEVELS, default='neutral')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        get_latest_by = 'timestamp'
    
    def __str__(self):
        return f"Sentiment: {self.get_level_display()} ({self.score})"


class Asset(models.Model):
    ASSET_TYPES = [
        ('crypto', 'Cryptocurrency'),
        ('stock', 'Stock'),
        ('forex', 'Forex'),
        ('commodity', 'Commodity'),
    ]
    
    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)
    exchange = models.CharField(max_length=50, blank=True)
    current_price = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    change_24h = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    volume_24h = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"


class PriceData(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='price_data')
    price = models.DecimalField(max_digits=20, decimal_places=2)
    volume = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    timestamp = models.DateTimeField()
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['asset', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.asset.symbol} - {self.price} @ {self.timestamp}"
