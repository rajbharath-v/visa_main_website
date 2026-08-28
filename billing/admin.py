"""billing/admin.py"""
from django.contrib import admin
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Client, Invoice, InvoiceLineItem, Supplier, PurchaseOrder, PurchaseOrderLineItem
from .views import invoice_pdf, invoice_excel, po_pdf, po_excel, po_docx
from .exports import (
    build_excel_response, build_pdf_response,
    build_po_excel_response, build_po_pdf_response,
)


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
        'invoice_no', 'document_type_badge', 'invoice_date', 'client', 'tax_badge',
        'grand_total_display', 'status_badge', 'download_links',
    ]
    list_filter     = ['document_type', 'status', 'tax_type', 'client']
    search_fields   = ['invoice_no', 'client__name', 'po_no', 'dc_no']
    date_hierarchy  = 'invoice_date'
    ordering        = ['-invoice_date', '-created_at']
    inlines         = [InvoiceLineItemInline]
    change_list_template = 'admin/billing/invoice/change_list.html'
    readonly_fields = [
        'subtotal', 'taxable_value', 'igst_amount', 'cgst_amount', 'sgst_amount',
        'round_off', 'grand_total', 'amount_in_words', 'created_at', 'updated_at',
    ]

    class Media:
        js = ('billing/js/proforma_prefill.js',)

    fieldsets = [
        ('Invoice Info', {
            'fields': ['document_type', 'invoice_no', 'invoice_date', 'status', 'client'],
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

    def document_type_badge(self, obj):
        if obj.document_type == 'proforma':
            return mark_safe('<span style="background:#ede9fe;color:#6d28d9;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700">Proforma</span>')
        return mark_safe('<span style="background:#e0f2fe;color:#0369a1;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700">Invoice</span>')
    document_type_badge.short_description = 'Type'

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
            path('statement/', self.admin_site.admin_view(self.invoice_statement_view), name='billing_invoice_statement'),
            path('statement/excel/', self.admin_site.admin_view(self.invoice_statement_excel), name='billing_invoice_statement_excel'),
            path('statement/pdf/', self.admin_site.admin_view(self.invoice_statement_pdf), name='billing_invoice_statement_pdf'),
        ]
        return custom + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['statement_qs'] = request.GET.urlencode()
        return super().changelist_view(request, extra_context=extra_context)

    def _period_label(self, request):
        import calendar
        year = request.GET.get('invoice_date__year')
        month = request.GET.get('invoice_date__month')
        if year and month:
            return f'{calendar.month_name[int(month)]} {year}'
        return 'All Invoices'

    def invoice_statement_view(self, request):
        cl = self.get_changelist_instance(request)
        qs = cl.get_queryset(request).filter(document_type='invoice').prefetch_related('line_items').order_by('invoice_no')
        total = sum(inv.grand_total for inv in qs)

        base_params = request.GET.copy()
        base_params.pop('status', None)

        def qs_for(status=None):
            params = base_params.copy()
            if status:
                params['status'] = status
            return params.urlencode()

        context = dict(
            self.admin_site.each_context(request),
            title='Invoice Statement',
            invoices=qs,
            total=total,
            count=qs.count(),
            period=self._period_label(request),
            statement_qs=request.GET.urlencode(),
            qs_all=qs_for(),
            qs_draft=qs_for('draft'),
            qs_approved=qs_for('approved'),
            qs_cancelled=qs_for('cancelled'),
            current_status=request.GET.get('status', ''),
            opts=self.model._meta,
        )
        return TemplateResponse(request, 'admin/billing/invoice/statement.html', context)
    def invoice_statement_excel(self, request):
        cl = self.get_changelist_instance(request)
        qs = cl.get_queryset(request).filter(document_type='invoice').order_by('invoice_no')
        return build_excel_response(qs, self._period_label(request))

    def invoice_statement_pdf(self, request):
        cl = self.get_changelist_instance(request)
        qs = cl.get_queryset(request).filter(document_type='invoice').order_by('invoice_no')
        return build_pdf_response(qs, self._period_label(request))

    def invoice_pdf_view(self, request, pk):
        return invoice_pdf(request, pk)

    def invoice_excel_view(self, request, pk):
        return invoice_excel(request, pk)

    def save_formset(self, request, form, formset, change):
        """Ensure totals are recalculated after line items are saved/deleted via the inline."""
        super().save_formset(request, form, formset, change)
        if formset.model is InvoiceLineItem:
            form.instance.recalculate_totals()


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display  = ['name', 'contact_person', 'phone', 'city', 'state', 'gstin', 'is_active']
    list_filter   = ['is_active', 'state']
    search_fields = ['name', 'contact_person', 'phone', 'email', 'gstin', 'city', 'state']
    ordering      = ['name']


class PurchaseOrderLineItemInline(admin.TabularInline):
    model = PurchaseOrderLineItem
    extra = 1
    fields = ['description', 'qty', 'unit', 'unit_price', 'amount']
    readonly_fields = ['amount']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display    = [
        'po_no', 'po_date', 'supplier', 'currency_badge', 'tax_badge_po',
        'grand_total_display_po', 'status_badge_po', 'download_links_po',
    ]
    list_filter     = ['currency', 'status', 'tax_type', 'supplier']
    search_fields   = ['po_no', 'supplier__name', 'contact_person']
    date_hierarchy  = 'po_date'
    ordering        = ['-po_date', '-created_at']
    inlines         = [PurchaseOrderLineItemInline]
    change_list_template = 'admin/billing/purchaseorder/change_list.html'
    readonly_fields = [
        'subtotal', 'taxable_value', 'igst_amount', 'cgst_amount', 'sgst_amount',
        'round_off', 'grand_total', 'created_at', 'updated_at',
    ]

    fieldsets = [
        ('PO Info', {
            'fields': ['po_no', 'po_date', 'status', 'supplier', 'contact_person', 'contact_email'],
        }),
        ('Reference', {
            'fields': ['ref_no', 'ref_date'],
        }),
        ('Currency & Tax', {
            'fields': ['currency', 'tax_type', 'igst_rate', 'cgst_rate', 'sgst_rate'],
        }),
        ('Delivery & Payment', {
            'fields': ['from_place', 'to_place', 'delivery_date', 'payment_terms'],
        }),
        ('Totals (auto-calculated)', {
            'fields': [
                'subtotal', 'taxable_value', 'igst_amount', 'cgst_amount',
                'sgst_amount', 'round_off', 'grand_total',
            ],
        }),
        ('Prepared By & Notes', {
            'fields': ['prepared_by', 'notes'],
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]

    def currency_badge(self, obj):
        colors = {'INR': ('#dcfce7', '#166534'), 'USD': ('#dbeafe', '#1d4ed8'), 'EUR': ('#fef3c7', '#92400e')}
        bg, fg = colors.get(obj.currency, ('#f3f4f6', '#374151'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700">{}</span>',
            bg, fg, obj.currency,
        )
    currency_badge.short_description = 'Currency'

    def tax_badge_po(self, obj):
        resolved = obj.resolved_tax_type()
        labels = {'igst': 'IGST 18%', 'cgst_sgst': 'CGST 9% + SGST 9%', 'none': 'No Tax'}
        return mark_safe(f'<span style="background:#ede9fe;color:#6d28d9;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700">{labels.get(resolved, resolved)}</span>')
    tax_badge_po.short_description = 'Tax'

    def status_badge_po(self, obj):
        colors = {
            'draft':     ('#fef3c7', '#92400e'),
            'approved':  ('#d1fae5', '#065f46'),
            'cancelled': ('#fee2e2', '#991b1b'),
        }
        bg, fg = colors.get(obj.status, ('#f3f4f6', '#374151'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700">{}</span>',
            bg, fg, obj.get_status_display(),
        )
    status_badge_po.short_description = 'Status'

    def grand_total_display_po(self, obj):
        return format_html(
            '<span style="font-weight:600;font-variant-numeric:tabular-nums">{} {}</span>',
            obj.currency_symbol, f'{obj.grand_total:,.2f}',
        )
    grand_total_display_po.short_description = 'Grand Total'

    def download_links_po(self, obj):
        if not obj.pk:
            return '—'
        pdf_url = reverse('admin:billing_po_pdf', args=[obj.pk])
        excel_url = reverse('admin:billing_po_excel', args=[obj.pk])
        docx_url = reverse('admin:billing_po_docx', args=[obj.pk])
        return format_html(
            '<a href="{}" target="_blank" style="background:#3b6fd4;color:#fff;padding:3px 10px;'
            'border-radius:6px;font-size:11px;font-weight:600;text-decoration:none;margin-right:4px">⬇ PDF</a>'
            '<a href="{}" style="background:#16a34a;color:#fff;padding:3px 10px;'
            'border-radius:6px;font-size:11px;font-weight:600;text-decoration:none;margin-right:4px">⬇ Excel</a>'
            '<a href="{}" style="background:#2563eb;color:#fff;padding:3px 10px;'
            'border-radius:6px;font-size:11px;font-weight:600;text-decoration:none">⬇ Word</a>',
            pdf_url, excel_url, docx_url,
        )
    download_links_po.short_description = 'Download'

    def get_urls(self):
        custom = [
            path('<int:pk>/pdf/', self.admin_site.admin_view(self.po_pdf_view), name='billing_po_pdf'),
            path('<int:pk>/excel/', self.admin_site.admin_view(self.po_excel_view), name='billing_po_excel'),
            path('<int:pk>/docx/', self.admin_site.admin_view(self.po_docx_view), name='billing_po_docx'),
            path('statement/', self.admin_site.admin_view(self.po_statement_view), name='billing_po_statement'),
            path('statement/excel/', self.admin_site.admin_view(self.po_statement_excel), name='billing_po_statement_excel'),
            path('statement/pdf/', self.admin_site.admin_view(self.po_statement_pdf), name='billing_po_statement_pdf'),
        ]
        return custom + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['statement_qs'] = request.GET.urlencode()
        return super().changelist_view(request, extra_context=extra_context)

    def _period_label_po(self, request):
        import calendar
        year = request.GET.get('po_date__year')
        month = request.GET.get('po_date__month')
        if year and month:
            return f'{calendar.month_name[int(month)]} {year}'
        return 'All Purchase Orders'

    def po_statement_view(self, request):
        cl = self.get_changelist_instance(request)
        qs = cl.get_queryset(request).prefetch_related('line_items').order_by('po_no')

        totals_by_currency = {}
        for po in qs:
            totals_by_currency[po.currency] = totals_by_currency.get(po.currency, 0) + po.grand_total

        base_params = request.GET.copy()
        base_params.pop('status', None)

        def qs_for(status=None):
            params = base_params.copy()
            if status:
                params['status'] = status
            return params.urlencode()

        context = dict(
            self.admin_site.each_context(request),
            title='Purchase Order Statement',
            pos=qs,
            totals_by_currency=totals_by_currency,
            count=qs.count(),
            period=self._period_label_po(request),
            statement_qs=request.GET.urlencode(),
            qs_all=qs_for(),
            qs_draft=qs_for('draft'),
            qs_approved=qs_for('approved'),
            qs_cancelled=qs_for('cancelled'),
            current_status=request.GET.get('status', ''),
            opts=self.model._meta,
        )
        return TemplateResponse(request, 'admin/billing/purchaseorder/statement.html', context)

    def po_statement_excel(self, request):
        cl = self.get_changelist_instance(request)
        return build_po_excel_response(cl.get_queryset(request).order_by('po_no'), self._period_label_po(request))

    def po_statement_pdf(self, request):
        cl = self.get_changelist_instance(request)
        return build_po_pdf_response(cl.get_queryset(request).order_by('po_no'), self._period_label_po(request))

    def po_pdf_view(self, request, pk):
        return po_pdf(request, pk)

    def po_excel_view(self, request, pk):
        return po_excel(request, pk)

    def po_docx_view(self, request, pk):
        return po_docx(request, pk)

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if formset.model is PurchaseOrderLineItem:
            form.instance.recalculate_totals()