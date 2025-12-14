from django.contrib import admin
from .models import DetectedPattern, PatternAlert, PatternHistory


@admin.register(DetectedPattern)
class DetectedPatternAdmin(admin.ModelAdmin):
    list_display = ['pattern_type', 'asset', 'timeframe', 'confidence', 'status', 'detected_at']
    list_filter = ['pattern_type', 'status', 'detected_at']
    search_fields = ['asset__symbol']


@admin.register(PatternAlert)
class PatternAlertAdmin(admin.ModelAdmin):
    list_display = ['alert_type', 'asset', 'confidence', 'created_at']
    list_filter = ['alert_type', 'created_at']
    search_fields = ['asset__symbol']


@admin.register(PatternHistory)
class PatternHistoryAdmin(admin.ModelAdmin):
    list_display = ['pattern', 'predicted_price', 'actual_price', 'accuracy', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['pattern__asset__symbol']
