from django.contrib import admin
from .models import Forecast, ForecastPoint, Pattern


class ForecastPointInline(admin.TabularInline):
    model = ForecastPoint
    extra = 0


class PatternInline(admin.TabularInline):
    model = Pattern
    extra = 0


@admin.register(Forecast)
class ForecastAdmin(admin.ModelAdmin):
    list_display = ['asset', 'user', 'prediction_horizon_days', 'confidence_score', 'created_at']
    list_filter = ['risk_tolerance', 'created_at']
    search_fields = ['asset__symbol', 'user__username']
    inlines = [ForecastPointInline, PatternInline]


@admin.register(ForecastPoint)
class ForecastPointAdmin(admin.ModelAdmin):
    list_display = ['forecast', 'date', 'predicted_price']
    list_filter = ['date']
    search_fields = ['forecast__asset__symbol']


@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    list_display = ['pattern_type', 'asset', 'timeframe', 'match_percentage', 'detected_at']
    list_filter = ['pattern_type', 'timeframe', 'detected_at']
    search_fields = ['asset__symbol']
