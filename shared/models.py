"""
shared/models.py
All product models + Enquiry used across all 3 VISA websites
"""
from django.db import models
from django.utils.text import slugify
from PIL import Image
import os
from visa_group.storage import CloudinaryRawStorage


class ProductDivision(models.Model):
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon        = models.CharField(max_length=50, default='ti-package',
                                   help_text='Tabler icon class e.g. ti-ripple')
    color       = models.CharField(max_length=20, default='#185FA5',
                                   help_text='Hex colour for UI accents')
    order       = models.PositiveIntegerField(default=0)
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Product Division'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductCategory(models.Model):
    division    = models.ForeignKey(ProductDivision, on_delete=models.CASCADE,
                                    related_name='categories')
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon        = models.CharField(max_length=50, default='ti-folder')
    order       = models.PositiveIntegerField(default=0)
    is_active   = models.BooleanField(default=True)
    # SEO
    meta_title  = models.CharField(max_length=60, blank=True)
    meta_desc   = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'

    def __str__(self):
        return f'{self.division.name} → {self.name}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    STOCK_CHOICES = [
        ('available',     'Available'),
        ('on_request',    'On Request'),
        ('discontinued',  'Discontinued'),
    ]

    category     = models.ForeignKey(ProductCategory, on_delete=models.CASCADE,
                                     related_name='products')
    name         = models.CharField(max_length=200)
    slug         = models.SlugField(unique=True, max_length=220)
    short_desc   = models.CharField(max_length=200, blank=True,
                                    help_text='One line shown on product card')
    description  = models.TextField(help_text='Full product description — min 150 words for SEO')
    specifications = models.JSONField(default=dict, blank=True,
                                      help_text='{"Flow Rate": "0–100 ml/min", "Voltage": "12V DC"}')
    applications = models.TextField(blank=True,
                                    help_text='Comma-separated: Lab, Pharma, Food & Beverage')
    price_label  = models.CharField(max_length=100, blank=True,
                                    help_text='e.g. "Get Best Quote" or "₹4,500 onwards"')
    stock_status = models.CharField(max_length=20, choices=STOCK_CHOICES,
                                    default='available')
    is_featured  = models.BooleanField(default=False,
                                       help_text='Show on homepage featured section')
    is_active    = models.BooleanField(default=True)
    # SEO fields
    meta_title   = models.CharField(max_length=60, blank=True,
                                    help_text='Max 60 chars — auto-generated if blank')
    meta_desc    = models.CharField(max_length=160, blank=True,
                                    help_text='Max 160 chars — shown in Google search results')
    meta_keywords = models.CharField(max_length=300, blank=True)
    pdf_brochure  = models.FileField(
        storage=CloudinaryRawStorage(),
        upload_to='product_pdfs/',
        blank=True,
        null=True,
        help_text='Upload product brochure PDF — shown as download button on product page'
    )
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        # Auto-generate SEO fields if blank
        if not self.meta_title:
            self.meta_title = f'{self.name} — VISA Pvt. Ltd Chennai'[:60]
        if not self.meta_desc:
            self.meta_desc = (
                f'{self.short_desc or self.name} | Manufacturer & supplier in Chennai, India. '
                f'Get best quote from VISA Pvt. Ltd.'
            )[:160]
        super().save(*args, **kwargs)

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()

    @property
    def division(self):
        return self.category.division

    def get_applications_list(self):
        return [a.strip() for a in self.applications.split(',') if a.strip()]


class ProductImage(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE,
                                   related_name='images')
    image      = models.ImageField(upload_to='products/%Y/%m/')
    alt_text   = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order      = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.product.name} — image {self.order}'

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = f'{self.product.name} — VISA Pvt. Ltd Chennai'
        super().save(*args, **kwargs)
        # Convert to WebP for performance
        self._convert_to_webp()

    def _convert_to_webp(self):
        try:
            img_path = self.image.path
            if not img_path.lower().endswith('.webp'):
                img = Image.open(img_path)
                webp_path = os.path.splitext(img_path)[0] + '.webp'
                img.save(webp_path, 'WEBP', quality=85)
        except Exception:
            pass


class Enquiry(models.Model):
    SOURCE_CHOICES = [
        ('visa_main',  'VISA Main Site'),
        ('pump_site',  'Peristaltic Pump Site'),
        ('hart_site',  'HART Communicator Site'),
    ]
    STATUS_CHOICES = [
        ('new',         'New'),
        ('contacted',   'Contacted'),
        ('converted',   'Converted'),
        ('closed',      'Closed'),
    ]

    # Contact info
    name        = models.CharField(max_length=100)
    company     = models.CharField(max_length=150, blank=True)
    phone       = models.CharField(max_length=20)
    email       = models.EmailField(blank=True)
    city        = models.CharField(max_length=100, blank=True)
    country     = models.CharField(max_length=100, default='India')

    # Enquiry details
    product     = models.ForeignKey(Product, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='enquiries')
    product_name = models.CharField(max_length=200, blank=True,
                                    help_text='Filled if product not in DB')
    message     = models.TextField(blank=True, default='')
    quantity    = models.CharField(max_length=50, blank=True)

    # Meta
    source      = models.CharField(max_length=20, choices=SOURCE_CHOICES,
                                   default='visa_main')
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                   default='new')
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    notes       = models.TextField(blank=True, help_text='Internal notes')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Enquiry / Lead'
        verbose_name_plural = 'Enquiries / Leads'

    def __str__(self):
        return f'{self.name} — {self.product_name or (self.product.name if self.product else "General")} ({self.created_at.strftime("%d %b %Y")})'


class BlogPost(models.Model):
    title      = models.CharField(max_length=200)
    slug       = models.SlugField(unique=True)
    excerpt    = models.CharField(max_length=300)
    content    = models.TextField()
    image      = models.ImageField(upload_to='blog/', blank=True)
    meta_title = models.CharField(max_length=60, blank=True)
    meta_desc  = models.CharField(max_length=160, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
