"""office/admin.py"""
from django.contrib import admin
from django.utils.html import format_html, mark_safe
from .models import Staff, VoucherDebitAccount, Voucher


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
    ordering      = ['-date', '-created_at']
    readonly_fields = ['amount_in_words', 'created_at', 'updated_at']

    fieldsets = [
        ('Voucher Info', {
            'fields': ['voucher_type', 'voucher_no', 'date', 'status'],
        }),
        ('Payment Details', {
            'fields': ['debit_account', 'pay_to', 'account_no', 'amount', 'amount_in_words', 'towards'],
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
