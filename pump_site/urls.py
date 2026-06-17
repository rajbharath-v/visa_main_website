"""pump_site/urls.py — peristalticpump.in (coming soon)"""
from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from shared.views_errors import error_400, error_403, error_404, error_500


def coming_soon(request):
    return render(request, 'pump_site/coming_soon.html', {
        'meta_title': 'Peristaltic Pump — VISA Pvt. Ltd Chennai',
        'meta_desc': 'Industrial Peristaltic Pumps by VISA Pvt. Ltd, Chennai. Coming soon.',
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', coming_soon, name='pump_home'),
]

handler400 = error_400
handler403 = error_403
handler404 = error_404
handler500 = error_500
