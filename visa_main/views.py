"""visa_main/views.py — All views for visapvtltd.co.in"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Prefetch
from shared.models import ProductDivision, ProductCategory, Product, Enquiry, BlogPost
from shared.forms import EnquiryForm
from shared.seo import organization_schema, website_schema, product_schema, breadcrumb_schema
from shared.emails import send_enquiry_notification


# ─── HOMEPAGE ───────────────────────────────────────────────────────────────

def home(request):
    featured = Product.objects.filter(is_featured=True, is_active=True).select_related(
        'category__division'
    ).prefetch_related('images')[:8]

    categories_qs = ProductCategory.objects.filter(is_active=True).select_related(
        'division'
    ).prefetch_related(
        Prefetch(
            'products',
            queryset=Product.objects.filter(is_active=True).select_related(
                'category__division'
            ).prefetch_related('images'),
            to_attr='active_products',
        )
    )
    categories_with_products = [c for c in categories_qs if c.active_products]

    divisions  = ProductDivision.objects.filter(is_active=True).prefetch_related(
                     'categories'
                 )
    stats = {
        'years':    35,
        'products': Product.objects.filter(is_active=True).count(),
        'countries': 5,
        'sqft':     5250,
    }
    form = EnquiryForm()
    return render(request, 'visa_main/pages/home.html', {
        'featured':                 featured,
        'categories_with_products': categories_with_products,
        'divisions':  divisions,
        'stats':      stats,
        'form':       form,
        'meta_title': 'VISA Pvt. Ltd — Process Control Instruments & Fluid Handling, Chennai',
        'meta_desc':  'Manufacturer of peristaltic pumps, flow meters, pressure transmitters & IoT modules. 35+ years. Exporting to 5 countries. Get a quote today.',
        'org_schema': organization_schema(),
        'web_schema': website_schema(),
        'is_home':    True,
    })


# ─── PRODUCTS ───────────────────────────────────────────────────────────────

def products(request):
    division_slug  = request.GET.get('division')
    category_slug  = request.GET.get('category')
    search_query   = request.GET.get('q', '').strip()

    all_products = Product.objects.filter(is_active=True).select_related(
        'category__division'
    ).prefetch_related('images')

    active_division = None
    active_category = None

    if division_slug:
        active_division = get_object_or_404(ProductDivision, slug=division_slug)
        all_products = all_products.filter(category__division=active_division)

    if category_slug:
        active_category = get_object_or_404(ProductCategory, slug=category_slug)
        all_products    = all_products.filter(category=active_category)
        active_division = active_category.division

    if search_query:
        all_products = all_products.filter(name__icontains=search_query) | \
                       all_products.filter(short_desc__icontains=search_query) | \
                       all_products.filter(description__icontains=search_query)

    divisions  = ProductDivision.objects.filter(is_active=True).prefetch_related('categories')
    categories = active_division.categories.filter(is_active=True) if active_division else []

    # Build meta
    if active_category:
        meta_title = f'{active_category.name} — VISA Pvt. Ltd Chennai'
        meta_desc  = active_category.meta_desc or f'Buy {active_category.name} from VISA Pvt. Ltd, Chennai. Manufacturer & supplier in India.'
    elif active_division:
        meta_title = f'{active_division.name} — VISA Pvt. Ltd'
        meta_desc  = f'Complete range of {active_division.name} from VISA Pvt. Ltd, Chennai. 35+ years manufacturing experience.'
    else:
        meta_title = 'All Products — VISA Pvt. Ltd | Process Control & Fluid Handling'
        meta_desc  = 'Browse 60+ industrial products — flow meters, peristaltic pumps, pressure transmitters, IoT modules from VISA Pvt. Ltd Chennai.'

    return render(request, 'visa_main/pages/products.html', {
        'products':         all_products,
        'divisions':        divisions,
        'categories':       categories,
        'active_division':  active_division,
        'active_category':  active_category,
        'search_query':     search_query,
        'total_count':      all_products.count(),
        'meta_title':       meta_title,
        'meta_desc':        meta_desc,
    })


def product_detail(request, slug):
    product  = get_object_or_404(Product, slug=slug, is_active=True)
    related  = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product.id).prefetch_related('images')[:4]

    form = EnquiryForm(initial={'product_name': product.name})

    base_url = f'{request.scheme}://{request.get_host()}'
    breadcrumbs = [
        ('Home',                    f'{base_url}/'),
        ('Products',                f'{base_url}/products/'),
        (product.category.division.name, f'{base_url}/products/?division={product.category.division.slug}'),
        (product.category.name,    f'{base_url}/products/?category={product.category.slug}'),
        (product.name,             None),
    ]

    return render(request, 'visa_main/pages/product_detail.html', {
        'product':    product,
        'related':    related,
        'form':       form,
        'images':     product.images.all(),
        'specs':      product.specifications,
        'apps_list':  product.get_applications_list(),
        'meta_title': product.meta_title,
        'meta_desc':  product.meta_desc,
        'prod_schema': product_schema(product, request),
        'bc_schema':   breadcrumb_schema(breadcrumbs),
    })


def category_page(request, slug):
    category = get_object_or_404(ProductCategory, slug=slug, is_active=True)
    products_qs = Product.objects.filter(
        category=category, is_active=True
    ).prefetch_related('images')
    form = EnquiryForm()
    return render(request, 'visa_main/pages/category.html', {
        'category':   category,
        'products':   products_qs,
        'form':       form,
        'meta_title': category.meta_title or f'{category.name} — VISA Pvt. Ltd Chennai',
        'meta_desc':  category.meta_desc or f'Buy {category.name} from VISA Pvt. Ltd, Chennai.',
    })


# ─── ENQUIRY ────────────────────────────────────────────────────────────────

def _is_rate_limited(ip):
    """Block IPs that submit more than 3 enquiries in the last hour."""
    from django.utils import timezone
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(hours=1)
    count = Enquiry.objects.filter(ip_address=ip, created_at__gte=cutoff).count()
    return count >= 3


@require_POST
def submit_enquiry(request):
    ip = request.META.get('REMOTE_ADDR')
    if _is_rate_limited(ip):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Too many submissions. Please try again later.'}, status=429)
        messages.error(request, 'Too many submissions. Please try again later.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    form = EnquiryForm(request.POST)
    if form.is_valid():
        enquiry             = form.save(commit=False)
        enquiry.source      = 'visa_main'
        enquiry.ip_address  = ip
        product_slug = request.POST.get('product_slug')
        if product_slug:
            try:
                enquiry.product = Product.objects.get(slug=product_slug)
            except Product.DoesNotExist:
                pass
        enquiry.save()
        send_enquiry_notification(enquiry)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True,
                                 'message': 'Thank you! We will contact you within 24 hours.'})
        messages.success(request, 'Thank you! We will contact you within 24 hours.')
        return redirect('home')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    messages.error(request, 'Please fill all required fields.')
    return redirect(request.META.get('HTTP_REFERER', '/'))


# ─── STATIC PAGES ───────────────────────────────────────────────────────────

def about(request):
    return render(request, 'visa_main/pages/about.html', {
        'meta_title': 'About VISA Pvt. Ltd — 35 Years of Process Control Excellence, Chennai',
        'meta_desc':  'Learn about Virtual Instrumentation & Software Applications Pvt. Ltd — 35 years of manufacturing precision instruments in Chennai.',
    })


def projects(request):
    return render(request, 'visa_main/pages/projects.html', {
        'meta_title': 'Projects — Teletherm Instruments, Chennai | VISA Pvt. Ltd',
        'meta_desc':  'Our 5250 sqft facility in Chennai. Teletherm Instruments — 35 years of precision instrument projects.',
    })


def contact(request):
    form = EnquiryForm()
    return render(request, 'visa_main/pages/contact.html', {
        'form':       form,
        'meta_title': 'Contact VISA Pvt. Ltd — Get a Quote | Chennai',
        'meta_desc':  'Contact VISA Pvt. Ltd for peristaltic pumps, flow meters & process control instruments. Phone: +91 94453 50717. Chennai, India.',
    })


def blog_list(request):
    posts = BlogPost.objects.filter(is_published=True)
    return render(request, 'visa_main/pages/blog.html', {
        'posts':      posts,
        'meta_title': 'Blog — Process Control & Instrumentation Insights | VISA Pvt. Ltd',
        'meta_desc':  'Technical articles on process control, flow measurement, peristaltic pumps and industrial instrumentation from VISA Pvt. Ltd.',
    })


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    return render(request, 'visa_main/pages/blog_detail.html', {
        'post':       post,
        'meta_title': post.meta_title or post.title,
        'meta_desc':  post.meta_desc or post.excerpt,
    })


def robots_txt(request):
    content = """User-agent: *
Allow: /
Disallow: /admin/

Sitemap: https://www.visapvtltd.co.in/sitemap.xml
"""
    return HttpResponse(content, content_type='text/plain')
