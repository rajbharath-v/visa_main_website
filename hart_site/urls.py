"""hart_site/urls.py — hartcommunicator.in"""
from django.contrib import admin
from django.urls import path
from shared.views_admin import analytics_dashboard
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
