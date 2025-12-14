from django.urls import path
from . import views

app_name = 'forecast'

urlpatterns = [
    path('', views.index, name='index'),
    path('run/', views.run_forecast, name='run_forecast'),
    path('results/<int:forecast_id>/', views.results, name='results'),
    path('history/', views.history, name='history'),
]


