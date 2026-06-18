"""pump_site/urls.py — peristalticpump.in"""
from django.contrib import admin
from django.urls import path
from shared.views_errors import error_400, error_403, error_404, error_500
from . import views

urlpatterns = [
    path('admin/',                        admin.site.urls),
    path('',                              views.home,           name='pump_home'),
    path('products/',                     views.products,       name='pump_products'),
    path('products/<slug:slug>/',         views.product_detail, name='pump_product_detail'),
    path('about/',                        views.about,          name='pump_about'),
    path('contact/',                      views.contact,        name='pump_contact'),
    path('enquiry/submit/',               views.submit_enquiry, name='pump_submit_enquiry'),
    path('robots.txt',                    views.robots_txt,     name='pump_robots'),
    path('sitemap.xml',                   views.sitemap_xml,    name='pump_sitemap'),
]

handler400 = error_400
handler403 = error_403
handler404 = error_404
handler500 = error_500
