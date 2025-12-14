from django.contrib import admin
from .models import MarketIndicator, Signal, MarketSentiment, Asset, PriceData


@admin.register(MarketIndicator)
class MarketIndicatorAdmin(admin.ModelAdmin):
    list_display = ['indicator_type', 'value', 'change_percent', 'timestamp']
    list_filter = ['indicator_type', 'timestamp']
    readonly_fields = ['timestamp']


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = ['asset', 'signal_type', 'entry_price', 'target_price', 'confidence', 'created_at']
    list_filter = ['signal_type', 'created_at']
    search_fields = ['asset']


@admin.register(MarketSentiment)
class MarketSentimentAdmin(admin.ModelAdmin):
    list_display = ['score', 'level', 'timestamp']
    list_filter = ['level', 'timestamp']
    readonly_fields = ['timestamp']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'asset_type', 'current_price', 'change_24h', 'last_updated']
    list_filter = ['asset_type', 'last_updated']
    search_fields = ['symbol', 'name']


@admin.register(PriceData)
class PriceDataAdmin(admin.ModelAdmin):
    list_display = ['asset', 'price', 'volume', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['asset__symbol']
