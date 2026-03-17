"""
URL configuration for agrirobot project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from users.views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', dashboard, name='dashboard'),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('users/', include('users.urls')),
    path('devices/', include('devices.urls')),
    path('monitoring/', include('monitoring.urls')),
    path('ai/', include('ai_recognition.urls')),
    path('data/', include('data_analysis.urls')),
    path('control/', include('control.urls')),
    path('communication/', include('communication.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)