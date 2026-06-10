"""shared/admin.py — Complete admin for all VISA products and leads"""
from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
import csv
from .models import ProductDivision, ProductCategory, Product, ProductImage, Enquiry, BlogPost


class ProductImageInline(admin.TabularInline):
    model   = ProductImage
    extra   = 3
    fields  = ['image', 'alt_text', 'is_primary', 'order', 'preview']
    readonly_fields = ['preview']

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:64px;width:64px;object-fit:cover;border-radius:6px;"/>',
                obj.image.url
            )
        return '—'
    preview.short_description = 'Preview'


@admin.register(ProductDivision)
class ProductDivisionAdmin(admin.ModelAdmin):
    list_display  = ['name', 'slug', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'division', 'order', 'product_count', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter   = ['division', 'is_active']
    prepopulated_fields = {'slug': ('name',)}

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines       = [ProductImageInline]
    list_display  = ['thumbnail', 'name', 'category', 'division_name',
                     'stock_status', 'is_featured', 'is_active', 'enquiry_count']
    list_editable = ['stock_status', 'is_featured', 'is_active']
    list_filter   = ['category__division', 'category', 'stock_status',
                     'is_featured', 'is_active']
    search_fields = ['name', 'description', 'short_desc']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('Basic information', {
            'fields': ['category', 'name', 'slug', 'short_desc',
                       'description', 'applications', 'price_label',
                       'stock_status', 'is_featured', 'is_active']
        }),
        ('Specifications', {
            'fields': ['specifications'],
            'description': 'Add key-value specs: {"Flow Rate": "0–100 ml/min"}'
        }),
        ('SEO — critical for Google ranking', {
            'fields': ['meta_title', 'meta_desc', 'meta_keywords'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def thumbnail(self, obj):
        img = obj.primary_image
        if img:
            return format_html(
                '<img src="{}" style="height:44px;width:44px;object-fit:cover;border-radius:6px;"/>',
                img.image.url
            )
        return format_html('<div style="width:44px;height:44px;background:#E6F1FB;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:18px;">📦</div>')
    thumbnail.short_description = ''

    def division_name(self, obj):
        return obj.category.division.name
    division_name.short_description = 'Division'

    def enquiry_count(self, obj):
        count = obj.enquiries.count()
        if count:
            return format_html('<span style="color:#185FA5;font-weight:500">{} leads</span>', count)
        return '0'
    enquiry_count.short_description = 'Leads'


def export_enquiries_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="visa_leads.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Name', 'Company', 'Phone', 'Email', 'City',
                     'Product', 'Message', 'Source', 'Status'])
    for e in queryset:
        writer.writerow([
            e.created_at.strftime('%d/%m/%Y %H:%M'),
            e.name, e.company, e.phone, e.email, e.city,
            e.product.name if e.product else e.product_name,
            e.message, e.get_source_display(), e.get_status_display()
        ])
    return response
export_enquiries_csv.short_description = 'Export selected as CSV'


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display  = ['created_at', 'name', 'company', 'phone', 'email',
                     'product_display', 'source', 'status']
    list_editable = ['status']
    list_filter   = ['status', 'source', 'created_at']
    search_fields = ['name', 'company', 'email', 'phone']
    readonly_fields = ['created_at', 'ip_address']
    actions = [export_enquiries_csv]

    def product_display(self, obj):
        if obj.product:
            return obj.product.name
        return obj.product_name or '—'
    product_display.short_description = 'Product'

    def has_add_permission(self, request):
        return False  # Enquiries come from website only


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display  = ['title', 'is_published', 'created_at']
    list_editable = ['is_published']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'content']


# Admin site customization
admin.site.site_header  = 'VISA Pvt. Ltd — Admin Panel'
admin.site.site_title   = 'VISA Admin'
admin.site.index_title  = 'Manage Products, Leads & Content'
