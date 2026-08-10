"""office/admin.py"""
from django.contrib import admin
from django.utils.html import format_html, mark_safe
from .models import Staff, VoucherDebitAccount, Voucher
from django.urls import path
from django.template.response import TemplateResponse
from .exports import build_excel_response, build_pdf_response

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display  = ['name', 'designation', 'is_active']
    list_editable = ['designation', 'is_active']
    search_fields = ['name', 'designation']
    list_filter   = ['is_active']


@admin.register(VoucherDebitAccount)
class VoucherDebitAccountAdmin(admin.ModelAdmin):
    list_display  = ['name', 'voucher_type', 'is_active']
    list_editable = ['voucher_type', 'is_active']
    list_filter   = ['voucher_type', 'is_active']
    search_fields = ['name']


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display  = [
        'voucher_no', 'voucher_type_badge', 'date', 'pay_to',
        'debit_account', 'amount_display', 'prepared_by', 'status_badge', 'pdf_link',
    ]
    list_filter   = ['voucher_type', 'status', 'debit_account', 'prepared_by']
    search_fields = ['voucher_no', 'pay_to', 'towards', 'chq_no']
    date_hierarchy = 'date'
    ordering      = ['voucher_type', 'voucher_no'] 
    readonly_fields = ['amount_in_words', 'created_at', 'updated_at']

    fieldsets = [
        ('Voucher Info', {
            'fields': ['voucher_type', 'voucher_no', 'date', 'status'],
        }),
        ('Payment Details', {
            'fields': ['debit_account', 'pay_to', 'amount', 'amount_in_words', 'towards'],
        }),
        ('Bank / Cheque Details (Bank Voucher Only)', {
            'fields': ['chq_no', 'chq_date', 'drawn_on'],
            'classes': ['collapse'],
        }),
        ('Signatures', {
            'fields': ['prepared_by', 'checked_by', 'approved_by', 'received_by'],
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]

    def voucher_type_badge(self, obj):
        if obj.voucher_type == 'bank':
            return mark_safe('<span style="background:#dbeafe;color:#1d4ed8;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700">🏦 Bank</span>')
        return mark_safe('<span style="background:#d1fae5;color:#065f46;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700">💵 Cash</span>')
    voucher_type_badge.short_description = 'Type'

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

    def amount_display(self, obj):
        return format_html('<span style="font-weight:600;font-variant-numeric:tabular-nums">₹ {}</span>', f'{obj.amount:,.2f}')
    amount_display.short_description = 'Amount'

    def pdf_link(self, obj):
        if obj.pk:
            url = f'/office/voucher/{obj.pk}/pdf/'
            return format_html('<a href="{}" target="_blank" style="background:#3b6fd4;color:#fff;padding:3px 10px;border-radius:6px;font-size:11px;font-weight:600;text-decoration:none">⬇ PDF</a>', url)
        return '—'
    pdf_link.short_description = 'Download'

    change_list_template = 'admin/office/voucher/change_list.html'

    def get_urls(self):
        custom = [
            path('statement/', self.admin_site.admin_view(self.voucher_statement_view),
                 name='office_voucher_statement'),
            path('statement/excel/', self.admin_site.admin_view(self.voucher_statement_excel),
                 name='office_voucher_statement_excel'),
            path('statement/pdf/', self.admin_site.admin_view(self.voucher_statement_pdf),
                 name='office_voucher_statement_pdf'),
        ]
        return custom + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['statement_qs'] = request.GET.urlencode()
        return super().changelist_view(request, extra_context=extra_context)

    def _period_label(self, request):
        import calendar
        year = request.GET.get('date__year')
        month = request.GET.get('date__month')
        if year and month:
            return f'{calendar.month_name[int(month)]} {year}'
        return 'All Vouchers'

    def voucher_statement_view(self, request):
        cl = self.get_changelist_instance(request)
        qs = cl.get_queryset(request).order_by('voucher_type', 'voucher_no')
        total = sum(v.amount for v in qs)

        base_params = request.GET.copy()
        base_params.pop('voucher_type', None)

        def qs_for(vtype=None):
            params = base_params.copy()
            if vtype:
                params['voucher_type'] = vtype
            return params.urlencode()

        context = dict(
            self.admin_site.each_context(request),
            title='Voucher Statement',
            vouchers=qs,
            total=total,
            count=qs.count(),
            period=self._period_label(request),
            statement_qs=request.GET.urlencode(),
            qs_all=qs_for(),
            qs_bank=qs_for('bank'),
            qs_cash=qs_for('cash'),
            current_type=request.GET.get('voucher_type', ''),
            opts=self.model._meta,
        )
        return TemplateResponse(request, 'admin/office/voucher/statement.html', context)

    def voucher_statement_excel(self, request):
        cl = self.get_changelist_instance(request)
        return build_excel_response(cl.get_queryset(request), self._period_label(request))

    def voucher_statement_pdf(self, request):
        cl = self.get_changelist_instance(request)
        return build_pdf_response(cl.get_queryset(request), self._period_label(request))