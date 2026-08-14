"""billing/admin.py"""
from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Client, Invoice, InvoiceLineItem
from .views import invoice_pdf, invoice_excel


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display  = ['name', 'phone', 'city', 'state', 'gstin', 'is_active']
    list_filter   = ['is_active', 'state']
    search_fields = ['name', 'phone', 'gstin', 'city', 'state']
    ordering      = ['name']


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 1                      # start with 1 blank row — click "Add another" for as many as needed
    fields = ['description', 'model_no', 'hsn_code', 'serial_no', 'qty', 'unit', 'unit_price', 'amount']
    readonly_fields = ['amount']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display    = [
        'invoice_no', 'invoice_date', 'client', 'tax_badge',
        'grand_total_display', 'status_badge', 'download_links',
    ]
    list_filter     = ['status', 'tax_type', 'client']
    search_fields   = ['invoice_no', 'client__name', 'po_no', 'dc_no']
    date_hierarchy  = 'invoice_date'
    ordering        = ['-invoice_date', '-created_at']
    inlines         = [InvoiceLineItemInline]
    readonly_fields = [
        'subtotal', 'taxable_value', 'igst_amount', 'cgst_amount', 'sgst_amount',
        'round_off', 'grand_total', 'amount_in_words', 'created_at', 'updated_at',
    ]

    fieldsets = [
        ('Invoice Info', {
            'fields': ['invoice_no', 'invoice_date', 'status', 'client'],
        }),
        ('References', {
            'fields': ['po_no', 'po_date', 'dc_no', 'rr_lr_rpp_no', 'rr_lr_rpp_date', 'from_place', 'to_place'],
            'classes': ['collapse'],
        }),
        ('Tax', {
            'fields': ['tax_type', 'igst_rate', 'cgst_rate', 'sgst_rate'],
        }),
        ('Adjustments', {
            'fields': ['p_and_f', 'insurance', 'less_advance'],
        }),
        ('Totals (auto-calculated)', {
            'fields': [
                'subtotal', 'taxable_value', 'igst_amount', 'cgst_amount',
                'sgst_amount', 'round_off', 'grand_total', 'amount_in_words',
            ],
        }),
        ('Signatures & Notes', {
            'fields': ['prepared_by', 'authorized_by', 'notes'],
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]

    def tax_badge(self, obj):
        label = dict(obj.TAX_TYPE_CHOICES).get(obj.tax_type, obj.tax_type)
        resolved = obj.resolved_tax_type()
        resolved_label = 'IGST 18%' if resolved == 'igst' else 'CGST 9% + SGST 9%'
        text = resolved_label if obj.tax_type == 'auto' else label
        return mark_safe(f'<span style="background:#dbeafe;color:#1d4ed8;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700">{text}</span>')
    tax_badge.short_description = 'Tax'

    def status_badge(self, obj):
        colors = {
            'draft':     ('#fef3c7', '#92400e'),
            'approved':  ('#d1fae5', '#065f46'),
            'cancelled': ('#fee2e2', '#991b1b'),
        }
        bg, fg = colors.get(obj.status, ('#f3f4f6', '#374151'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700">{}</span>',
            bg, fg, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def grand_total_display(self, obj):
        return format_html('<span style="font-weight:600;font-variant-numeric:tabular-nums">₹ {}</span>', f'{obj.grand_total:,.2f}')
    grand_total_display.short_description = 'Grand Total'

    def download_links(self, obj):
        if not obj.pk:
            return '—'
        pdf_url = reverse('admin:billing_invoice_pdf', args=[obj.pk])
        excel_url = reverse('admin:billing_invoice_excel', args=[obj.pk])
        return format_html(
            '<a href="{}" target="_blank" style="background:#3b6fd4;color:#fff;padding:3px 10px;'
            'border-radius:6px;font-size:11px;font-weight:600;text-decoration:none;margin-right:4px">⬇ PDF</a>'
            '<a href="{}" style="background:#16a34a;color:#fff;padding:3px 10px;'
            'border-radius:6px;font-size:11px;font-weight:600;text-decoration:none">⬇ Excel</a>',
            pdf_url, excel_url,
        )
    download_links.short_description = 'Download'

    def get_urls(self):
        custom = [
            path('<int:pk>/pdf/', self.admin_site.admin_view(self.invoice_pdf_view), name='billing_invoice_pdf'),
            path('<int:pk>/excel/', self.admin_site.admin_view(self.invoice_excel_view), name='billing_invoice_excel'),
        ]
        return custom + super().get_urls()

    def invoice_pdf_view(self, request, pk):
        return invoice_pdf(request, pk)

    def invoice_excel_view(self, request, pk):
        return invoice_excel(request, pk)

    def save_formset(self, request, form, formset, change):
        """Ensure totals are recalculated after line items are saved/deleted via the inline."""
        super().save_formset(request, form, formset, change)
        if formset.model is InvoiceLineItem:
            form.instance.recalculate_totals()