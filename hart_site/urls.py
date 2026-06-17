"""hart_site/urls.py — hartcommunicator.in"""
from django.contrib import admin
from django.urls import path
from shared.views_admin import analytics_dashboard
from shared.views_errors import error_400, error_403, error_404, error_500
from . import views

urlpatterns = [
    path('admin/analytics/', analytics_dashboard, name='hart_admin_analytics'),
    path('admin/',           admin.site.urls),
    path('',                              views.home,           name='hart_home'),
    path('products/',                     views.products,       name='hart_products'),
    path('products/<slug:slug>/',         views.product_detail, name='hart_product_detail'),
    path('contact/',                      views.contact,        name='hart_contact'),
    path('enquiry/submit/',               views.submit_enquiry, name='hart_submit_enquiry'),
]

# Error handlers must be defined in the urlconf that Django is using for the request
handler400 = error_400
handler403 = error_403
handler404 = error_404
handler500 = error_500
