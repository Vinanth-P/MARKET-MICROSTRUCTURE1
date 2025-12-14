from django.urls import path
from . import api

app_name = 'dashboard_api'

urlpatterns = [
    path('market-overview/', api.market_overview, name='market_overview'),
    path('signals/', api.signals, name='signals'),
    path('sentiment/', api.sentiment, name='sentiment'),
    path('price-data/<str:symbol>/', api.price_data, name='price_data'),
]


