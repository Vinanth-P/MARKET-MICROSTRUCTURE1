"""
URL configuration for market_microstructure project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('forecast/', include('forecast.urls')),
    path('patterns/', include('patterns.urls')),
    path('api/dashboard/', include('dashboard.api_urls')),
    path('api/forecast/', include('forecast.api_urls')),
    path('api/patterns/', include('patterns.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
