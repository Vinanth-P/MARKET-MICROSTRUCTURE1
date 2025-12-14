from django.urls import path
from . import views

app_name = 'patterns'

urlpatterns = [
    path('', views.live, name='live'),
    path('detect/', views.detect_patterns, name='detect'),
    path('history/', views.history_view, name='history'),
    path('config/', views.config, name='config'),
]


