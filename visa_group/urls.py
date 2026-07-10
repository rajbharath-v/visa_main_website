"""visa_group/urls.py — domain-based routing"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from shared.views_admin import analytics_dashboard
from shared.views_errors import error_400, error_403, error_404, error_500

urlpatterns = [
    path('admin/analytics/', analytics_dashboard, name='admin_analytics'),
    path('admin/', admin.site.urls),
    path('office/', include('office.urls')),
    path('', include('visa_main.urls')),
]

# Custom error handlers
handler400 = error_400
handler403 = error_403
handler404 = error_404
handler500 = error_500

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
