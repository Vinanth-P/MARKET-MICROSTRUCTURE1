from django.urls import path
from . import api

app_name = 'patterns_api'

urlpatterns = [
    path('detect/', api.detect_patterns_api, name='detect'),
    path('live/', api.live_alerts, name='live'),
    path('history/', api.pattern_history_api, name='history'),
]


