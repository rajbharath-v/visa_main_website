"""billing/models.py — Invoice management for VISA Pvt. Ltd (Client / Invoice / InvoiceLineItem)"""
import re
from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from office.models import _amount_to_words, Staff   # reuse existing helper + Staff


VISA_STATE = 'tamil nadu'   # used to auto-detect intrastate vs interstate


class Client(models.Model):
    """Shared customer record — reusable for Invoice, and future Quotation / DC."""
    name       = models.CharField(max_length=200)
    address    = models.TextField()
    phone      = models.CharField(max_length=20, blank=True)
    gstin      = models.CharField(max_length=20, blank=True, verbose_name='GSTIN')
    city       = models.CharField(max_length=100, blank=True)
    state      = models.CharField(max_length=100, blank=True)
    is_active  = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Client'
        verbose_name_plural = 'Clients'
        ordering             = ['name']

    def __str__(self):
        return self.name

    @property
    def is_same_state_as_visa(self):
        return (self.state or '').strip().lower() in (VISA_STATE, 'tamilnadu', 'tn')


class Invoice(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('invoice',  'Invoice'),
        ('proforma', 'Proforma Invoice'),
    ]
    TAX_TYPE_CHOICES = [
        ('auto',       'Auto (based on client state)'),
        ('igst',       'IGST 18%'),
        ('cgst_sgst',  'CGST 9% + SGST 9%'),
    ]
    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('approved',  'Approved'),
        ('cancelled', 'Cancelled'),
    ]

    # Core
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPE_CHOICES, default='invoice')
    invoice_no    = models.CharField(max_length=20, blank=True, verbose_name='Invoice No.')
    invoice_date  = models.DateField(default=timezone.now)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Bill to
    client        = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='invoices')

    # References
    po_no         = models.CharField(max_length=100, blank=True, verbose_name='Your PO No.')
    po_date       = models.DateField(null=True, blank=True, verbose_name='PO Date')
    dc_no         = models.CharField(max_length=100, blank=True, verbose_name='DC No')
    rr_lr_rpp_no  = models.CharField(max_length=100, blank=True, verbose_name='RR/LR/RPP No')
    rr_lr_rpp_date = models.DateField(null=True, blank=True, verbose_name='RR/LR/RPP Date')
    from_place    = models.CharField(max_length=100, default='Chennai')
    to_place      = models.CharField(max_length=100, blank=True)

    # Tax
    tax_type      = models.CharField(max_length=10, choices=TAX_TYPE_CHOICES, default='auto')
    igst_rate     = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18.00'))
    cgst_rate     = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('9.00'))
    sgst_rate     = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('9.00'))

    # Adjustments
    p_and_f       = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='Add: P & F')
    insurance     = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    less_advance  = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='Less: Advance')

    # Computed / stored totals (recalculated whenever line items change)
    subtotal       = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    taxable_value   = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    igst_amount     = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    cgst_amount     = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    sgst_amount     = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    round_off       = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    grand_total     = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    amount_in_words = models.CharField(max_length=300, blank=True)

    # Signatures
    prepared_by   = models.ForeignKey(Staff, null=True, blank=True, on_delete=models.SET_NULL, related_name='prepared_invoices')
    authorized_by = models.ForeignKey(Staff, null=True, blank=True, on_delete=models.SET_NULL, related_name='authorized_invoices')

    notes         = models.TextField(blank=True, help_text='Leave blank to use the standard terms.')

    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering             = ['-invoice_date', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['document_type', 'invoice_no'],
                name='unique_invoice_no_per_document_type',
            ),
        ]

    def __str__(self):
        if self.document_type == 'proforma':
            return f'{self.invoice_no} — {self.client}'
        return f'INV-{self.invoice_no} — {self.client}'

    def resolved_tax_type(self):
        """Resolve 'auto' into an actual igst / cgst_sgst choice based on client's state."""
        if self.tax_type == 'auto':
            if self.client_id and self.client.is_same_state_as_visa:
                return 'cgst_sgst'
            return 'igst'
        return self.tax_type

    @property
    def tax_amount_display(self):
        """Combined tax amount regardless of whether it's IGST or CGST+SGST — for statements."""
        if self.resolved_tax_type() == 'igst':
            return self.igst_amount
        return self.cgst_amount + self.sgst_amount

    @property
    def product_summary_list(self):
        """List of line items, cached — used by the statement page to show first product + '+N more'."""
        return list(self.line_items.all())

    def clean(self):
        super().clean()
        if self.invoice_date:
            type_changed = False
            if self.pk:
                old = Invoice.objects.filter(pk=self.pk).values_list('document_type', flat=True).first()
                type_changed = old is not None and old != self.document_type

            if self.pk is None or type_changed:
                self.invoice_no = self._compute_invoice_no()

    def _compute_invoice_no(self):
        if self.document_type == 'proforma':
            prefix = 'PI-'

            entered_no = str(self.invoice_no).strip() if self.invoice_no else ''
            manual_number = None

            if entered_no:
                if entered_no.startswith(prefix):
                    number_part = entered_no[len(prefix):]
                    if number_part.isdigit():
                        manual_number = int(number_part)
                elif entered_no.isdigit():
                    manual_number = int(entered_no)
                else:
                    match = re.search(r'(\d+)$', entered_no)
                    if match:
                        manual_number = int(match.group(1))

            if manual_number is not None:
                return f'{prefix}{manual_number:03d}'

            last = Invoice.objects.filter(
            document_type='proforma',
            invoice_no__startswith=prefix,
            ).exclude(pk=self.pk).order_by('id').last()

            next_num = 1
            if last and last.invoice_no:
                match = re.search(r'(\d+)$', last.invoice_no)
                if match:
                    next_num = int(match.group(1)) + 1

            return f'{prefix}{next_num:03d}'

        elif self.document_type == 'invoice':
            if self.invoice_no:
                return str(self.invoice_no).strip()

            last = Invoice.objects.filter(
            document_type='invoice'
            ).exclude(pk=self.pk).order_by('id').last()

            next_num = 1
            if last and last.invoice_no:
                match = re.search(r'(\d+)$', last.invoice_no)
                if match:
                    next_num = int(match.group(1)) + 1

            return f'{next_num:03d}'

        return self.invoice_no
    def save(self, *args, **kwargs):
        type_changed = False
        if self.pk:
            old = Invoice.objects.filter(pk=self.pk).values_list('document_type', flat=True).first()
            type_changed = old is not None and old != self.document_type

        if self.pk is None or type_changed:
            self.invoice_no = self._compute_invoice_no()

        if not self.to_place and self.client_id:
            self.to_place = self.client.city or self.client.state or ''

        super().save(*args, **kwargs)

    def recalculate_totals(self):
        """Recompute subtotal, tax, round off and grand total from current line items."""
        items = list(self.line_items.all())
        subtotal = sum((item.amount for item in items), Decimal('0.00'))
        taxable_value = subtotal + (self.p_and_f or Decimal('0.00'))

        tax_type = self.resolved_tax_type()
        if tax_type == 'igst':
            igst_amount = (taxable_value * self.igst_rate / Decimal('100')).quantize(Decimal('0.01'))
            cgst_amount = Decimal('0.00')
            sgst_amount = Decimal('0.00')
            tax_total = igst_amount
        else:
            cgst_amount = (taxable_value * self.cgst_rate / Decimal('100')).quantize(Decimal('0.01'))
            sgst_amount = (taxable_value * self.sgst_rate / Decimal('100')).quantize(Decimal('0.01'))
            igst_amount = Decimal('0.00')
            tax_total = cgst_amount + sgst_amount

        raw_total = taxable_value + tax_total + (self.insurance or Decimal('0.00')) - (self.less_advance or Decimal('0.00'))
        rounded_total = raw_total.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        round_off = rounded_total - raw_total
        words = _amount_to_words(int(rounded_total)) + ' Only' if rounded_total else ''

        # Use .update() to avoid re-triggering save()/signals recursively
        Invoice.objects.filter(pk=self.pk).update(
            subtotal=subtotal,
            taxable_value=taxable_value,
            igst_amount=igst_amount,
            cgst_amount=cgst_amount,
            sgst_amount=sgst_amount,
            round_off=round_off,
            grand_total=rounded_total,
            amount_in_words=words,
        )


class InvoiceLineItem(models.Model):
    invoice     = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    description = models.CharField(max_length=300, verbose_name='Item / Description')
    model_no    = models.CharField(max_length=100, blank=True, verbose_name='Model')
    hsn_code    = models.CharField(max_length=30, blank=True, verbose_name='HSN Code')
    serial_no   = models.CharField(max_length=200, blank=True, verbose_name='Serial No(s)')
    qty         = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    unit        = models.CharField(max_length=20, default='Nos')
    unit_price  = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    amount      = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)

    class Meta:
        verbose_name        = 'Line Item'
        verbose_name_plural = 'Line Items'
        ordering             = ['id']

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):
        self.amount = (self.qty or Decimal('0')) * (self.unit_price or Decimal('0'))
        super().save(*args, **kwargs)


@receiver(post_save, sender=InvoiceLineItem)
@receiver(post_delete, sender=InvoiceLineItem)
def _recalc_invoice_totals(sender, instance, **kwargs):
    if instance.invoice_id:
        instance.invoice.recalculate_totals()

# ---------------------------------------------------------------------------
# PURCHASE ORDER
# ---------------------------------------------------------------------------
CURRENCY_SYMBOLS = {
    'INR': '₹',
    'USD': '$',
    'EUR': '€',
}


class Supplier(models.Model):
    """Vendor VISA purchases from - separate from Client (who VISA sells to)."""
    name       = models.CharField(max_length=200)
    address    = models.TextField()
    email      = models.EmailField(blank=True)
    phone      = models.CharField(max_length=20, blank=True)
    contact_person = models.CharField(max_length=150, blank=True)
    gstin      = models.CharField(max_length=20, blank=True, verbose_name='GSTIN')
    city       = models.CharField(max_length=100, blank=True)
    state      = models.CharField(max_length=100, blank=True)
    is_active  = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Supplier'
        verbose_name_plural = 'Suppliers'
        ordering             = ['name']

    def __str__(self):
        return self.name

    @property
    def is_same_state_as_visa(self):
        return (self.state or '').strip().lower() in (VISA_STATE, 'tamilnadu', 'tn')


class PurchaseOrder(models.Model):
    CURRENCY_CHOICES = [
        ('INR', '₹ INR'),
        ('USD', '$ USD'),
        ('EUR', '€ EUR'),
    ]
    TAX_TYPE_CHOICES = [
        ('auto',       'Auto (based on supplier state)'),
        ('igst',       'IGST 18%'),
        ('cgst_sgst',  'CGST 9% + SGST 9%'),
        ('none',       'NA (No GST)'),
    ]
    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('approved',  'Approved'),
        ('cancelled', 'Cancelled'),
    ]

    # Core
    po_no       = models.CharField(max_length=30, blank=True, verbose_name='PO Ref No.')
    po_date     = models.DateField(default=timezone.now)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Reference — supplier's own quotation/reference this PO is placed against
    ref_no      = models.CharField(max_length=100, blank=True, verbose_name='Ref No.')
    ref_date    = models.DateField(null=True, blank=True, verbose_name='Ref Date')

    # Supplier
    supplier        = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    contact_person   = models.CharField(max_length=150, blank=True)
    contact_email    = models.EmailField(blank=True)

    # Currency
    currency    = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')

    # From / To
    from_place  = models.CharField(max_length=100, default='Chennai')
    to_place    = models.CharField(max_length=100, blank=True)

    # Tax - only meaningful when currency == 'INR'
    tax_type    = models.CharField(max_length=10, choices=TAX_TYPE_CHOICES, default='auto')
    igst_rate   = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18.00'))
    cgst_rate   = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('9.00'))
    sgst_rate   = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('9.00'))

    # Delivery & payment
    delivery_date   = models.DateField(null=True, blank=True, verbose_name='Delivery Date')
    payment_terms   = models.CharField(max_length=300, blank=True, default='100% advance')

    # Legacy fields — kept for old records, no longer shown in the form or documents
    delivery       = models.CharField(max_length=100, blank=True, default='2-3 days')
    freight         = models.CharField(max_length=150, blank=True, default='Our Scope')

    # Computed / stored totals
    subtotal        = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    taxable_value    = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    igst_amount      = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    cgst_amount      = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    sgst_amount      = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    round_off        = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    grand_total      = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    prepared_by  = models.ForeignKey(Staff, null=True, blank=True, on_delete=models.SET_NULL, related_name='prepared_pos')

    notes        = models.TextField(blank=True, help_text='Leave blank to use the standard notes.')

    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'
        ordering             = ['-po_date', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['po_no'], name='unique_po_no'),
        ]

    def __str__(self):
        return f'{self.po_no} - {self.supplier}'

    def resolved_tax_type(self):
        """Resolve 'auto' based on supplier's state. No tax at all for foreign currency."""
        if self.currency != 'INR':
            return 'none'
        if self.tax_type == 'auto':
            if self.supplier_id and self.supplier.is_same_state_as_visa:
                return 'cgst_sgst'
            return 'igst'
        return self.tax_type

    def save(self, *args, **kwargs):
        if not self.po_no:
            prefix = 'VISA/MM/PUR/10/'
            last = PurchaseOrder.objects.filter(po_no__startswith=prefix).order_by('id').last()
            next_num = 1
            if last and last.po_no:
                match = re.search(r'(\d+)$', last.po_no)
                if match:
                    next_num = int(match.group(1)) + 1
            self.po_no = f'{prefix}{next_num:02d}'
        if not self.to_place and self.supplier_id:
            self.to_place = self.supplier.city or self.supplier.state or ''
        super().save(*args, **kwargs)

    def recalculate_totals(self):
        items = list(self.line_items.all())
        subtotal = sum((item.amount for item in items), Decimal('0.00'))
        taxable_value = subtotal

        resolved = self.resolved_tax_type()
        if resolved == 'igst':
            igst_amount = (taxable_value * self.igst_rate / Decimal('100')).quantize(Decimal('0.01'))
            cgst_amount = Decimal('0.00')
            sgst_amount = Decimal('0.00')
            tax_total = igst_amount
        elif resolved == 'cgst_sgst':
            cgst_amount = (taxable_value * self.cgst_rate / Decimal('100')).quantize(Decimal('0.01'))
            sgst_amount = (taxable_value * self.sgst_rate / Decimal('100')).quantize(Decimal('0.01'))
            igst_amount = Decimal('0.00')
            tax_total = cgst_amount + sgst_amount
        else:
            igst_amount = Decimal('0.00')
            cgst_amount = Decimal('0.00')
            sgst_amount = Decimal('0.00')
            tax_total = Decimal('0.00')

        raw_total = taxable_value + tax_total
        rounded_total = raw_total.quantize(Decimal('1'), rounding=ROUND_HALF_UP) if self.currency == 'INR' else raw_total.quantize(Decimal('0.01'))
        round_off = rounded_total - raw_total

        PurchaseOrder.objects.filter(pk=self.pk).update(
            subtotal=subtotal,
            taxable_value=taxable_value,
            igst_amount=igst_amount,
            cgst_amount=cgst_amount,
            sgst_amount=sgst_amount,
            round_off=round_off,
            grand_total=rounded_total,
        )

    @property
    def currency_symbol(self):
        return CURRENCY_SYMBOLS.get(self.currency, self.currency)


class PurchaseOrderLineItem(models.Model):
    po          = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='line_items')
    description = models.CharField(max_length=300, verbose_name='Item')
    qty         = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    unit        = models.CharField(max_length=20, default='Nos')
    unit_price  = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal('0.00'))
    amount      = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'), editable=False)

    class Meta:
        verbose_name        = 'Line Item'
        verbose_name_plural = 'Line Items'
        ordering             = ['id']

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):
        self.amount = (self.qty or Decimal('0')) * (self.unit_price or Decimal('0'))
        super().save(*args, **kwargs)


@receiver(post_save, sender=PurchaseOrderLineItem)
@receiver(post_delete, sender=PurchaseOrderLineItem)
def _recalc_po_totals(sender, instance, **kwargs):
    if instance.po_id:
        instance.po.recalculate_totals()