"""visa_main/sitemaps.py"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from shared.models import Product, ProductCategory


class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority   = 0.9

    def items(self):
        return Product.objects.filter(is_active=True)

    def location(self, obj):
        return f'/products/{obj.slug}/'

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq = 'monthly'
    priority   = 0.7

    def items(self):
        return ProductCategory.objects.filter(is_active=True)

    def location(self, obj):
        return f'/category/{obj.slug}/'


class StaticSitemap(Sitemap):
    changefreq = 'monthly'
    priority   = 0.6

    def items(self):
        return ['home', 'products', 'about', 'manufacturing', 'contact', 'blog']

    def location(self, item):
        return reverse(item)
