"""office/models.py — Voucher management for VISA Pvt. Ltd"""
from django.db import models
from django.utils import timezone


class Staff(models.Model):
    name        = models.CharField(max_length=100)
    designation = models.CharField(max_length=100, blank=True)
    is_active   = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Staff'
        verbose_name_plural = 'Staff'
        ordering            = ['name']

    def __str__(self):
        return self.name


class VoucherDebitAccount(models.Model):
    VOUCHER_TYPE_CHOICES = [
        ('bank', 'Bank Voucher'),
        ('cash', 'Cash Voucher'),
        ('both', 'Both'),
    ]
    name         = models.CharField(max_length=150)
    voucher_type = models.CharField(max_length=10, choices=VOUCHER_TYPE_CHOICES, default='both')
    is_active    = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Debit Account'
        verbose_name_plural = 'Debit Accounts'
        ordering            = ['name']

    def __str__(self):
        return self.name


class Voucher(models.Model):
    VOUCHER_TYPE_CHOICES = [
        ('bank', 'Bank Voucher'),
        ('cash', 'Cash Voucher'),
    ]
    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('approved',  'Approved'),
        ('cancelled', 'Cancelled'),
    ]

    # Core
    voucher_type    = models.CharField(max_length=10, choices=VOUCHER_TYPE_CHOICES, default='bank')
    voucher_no      = models.CharField(max_length=20, unique=True, blank=True)
    date            = models.DateField(default=timezone.now)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Payment
    debit_account   = models.ForeignKey(VoucherDebitAccount, on_delete=models.PROTECT, related_name='vouchers')
    pay_to          = models.CharField(max_length=200)
    account_no      = models.CharField(max_length=100, blank=True, verbose_name='A/c (Account No)')
    amount          = models.DecimalField(max_digits=12, decimal_places=2)
    amount_in_words = models.CharField(max_length=300, blank=True)
    towards         = models.TextField()

    # Bank only
    chq_no          = models.CharField(max_length=50, blank=True, verbose_name='Cheque No')
    chq_date        = models.DateField(null=True, blank=True, verbose_name='Cheque Date')
    drawn_on        = models.CharField(max_length=150, blank=True, verbose_name='Drawn On (Bank)')

    # Signatures — all optional
    prepared_by     = models.ForeignKey(Staff, null=True, blank=True, on_delete=models.SET_NULL, related_name='prepared_vouchers')
    checked_by      = models.ForeignKey(Staff, null=True, blank=True, on_delete=models.SET_NULL, related_name='checked_vouchers')
    approved_by     = models.ForeignKey(Staff, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_vouchers')
    received_by     = models.ForeignKey(Staff, null=True, blank=True, on_delete=models.SET_NULL, related_name='received_vouchers')

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Voucher'
        verbose_name_plural = 'Vouchers'
        ordering            = ['-date', '-created_at']

    def __str__(self):
        return f'{self.voucher_no} — {self.pay_to}'

    def save(self, *args, **kwargs):
        if not self.voucher_no:
            prefix   = 'BV' if self.voucher_type == 'bank' else 'CV'
            last     = Voucher.objects.filter(voucher_type=self.voucher_type).order_by('id').last()
            next_num = (int(last.voucher_no.split('-')[1]) + 1) if last and last.voucher_no else 1
            self.voucher_no = f'{prefix}-{next_num:03d}'
        if self.amount and not self.amount_in_words:
            self.amount_in_words = _amount_to_words(int(self.amount)) + ' Only'
        super().save(*args, **kwargs)


def _amount_to_words(n):
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
            'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
            'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']

    def below_thousand(num):
        if num == 0:       return ''
        elif num < 20:     return ones[num]
        elif num < 100:    return tens[num // 10] + ((' ' + ones[num % 10]) if num % 10 else '')
        else:              return ones[num // 100] + ' Hundred' + ((' ' + below_thousand(num % 100)) if num % 100 else '')

    if n == 0:
        return 'Zero'
    parts = []
    if n >= 10000000:
        parts.append(below_thousand(n // 10000000) + ' Crore')
        n %= 10000000
    if n >= 100000:
        parts.append(below_thousand(n // 100000) + ' Lakh')
        n %= 100000
    if n >= 1000:
        parts.append(below_thousand(n // 1000) + ' Thousand')
        n %= 1000
    if n > 0:
        parts.append(below_thousand(n))
    return ' '.join(parts)
