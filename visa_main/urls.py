"""visa_main/urls.py"""
from django.urls import path
from django.contrib.sitemaps.views import sitemap
from . import views
from .sitemaps import ProductSitemap, CategorySitemap, StaticSitemap

sitemaps = {
    'products':   ProductSitemap,
    'categories': CategorySitemap,
    'static':     StaticSitemap,
}

urlpatterns = [
    path('',                         views.home,             name='home'),
    path('products/',                views.products,         name='products'),
    path('products/<slug:slug>/',    views.product_detail,   name='product_detail'),
    path('category/<slug:slug>/',    views.category_page,    name='category'),
    path('about/',                   views.about,            name='about'),
    path('manufacturing/',           views.manufacturing,    name='manufacturing'),
    path('contact/',                 views.contact,          name='contact'),
    path('blog/',                    views.blog_list,        name='blog'),
    path('blog/<slug:slug>/',        views.blog_detail,      name='blog_detail'),
    path('enquiry/submit/',          views.submit_enquiry,   name='submit_enquiry'),
    path('sitemap.xml',              sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt',               views.robots_txt,       name='robots_txt'),
]
