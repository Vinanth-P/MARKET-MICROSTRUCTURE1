from django.urls import path
from . import api

app_name = 'forecast_api'

urlpatterns = [
    path('run/', api.run_forecast_api, name='run'),
    path('backtest/run/', api.run_backtest_api, name='backtest_run'),
    path('<int:forecast_id>/', api.forecast_detail, name='detail'),
    path('history/', api.forecast_history, name='history'),
]


