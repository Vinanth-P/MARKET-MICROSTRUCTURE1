from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.overview, name='overview'),
    path('dashboard/', views.overview, name='overview_alt'),
    path('asset/<str:symbol>/', views.asset_detail, name='asset_detail'),
]

