"""hart_site/views.py — hart475communicator.com"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from shared.models import Product, Enquiry
from shared.forms import EnquiryForm
from shared.emails import send_enquiry_notification
from shared.seo import hart_organization_schema, product_schema, breadcrumb_schema

HART_DIVISION = 'hart-communicators'


def _hart_faq_schema():
    import json
    faqs = [
        {
            "question": "What is a HART Communicator?",
            "answer": "A HART Communicator is a handheld device used to configure, calibrate, and troubleshoot HART-enabled field instruments like transmitters, positioners, and flowmeters. The SK-660 supports all HART instruments using DD (Device Description) files."
        },
        {
            "question": "What is the price of SK-660 HART Communicator in India?",
            "answer": "The SK-660 HART Communicator is competitively priced for the Indian market. Contact VISA Pvt. Ltd Chennai at +91 94453 50717 for the latest price and bulk discounts."
        },
        {
            "question": "Is SK-660 intrinsically safe for hazardous areas?",
            "answer": "Yes, the SK-660 is certified Ex ib IICT4 Gb, making it safe for Zone 1 hazardous areas including oil & gas, chemical, and pharmaceutical plants."
        },
        {
            "question": "Does SK-660 support all HART instruments?",
            "answer": "Yes, the SK-660 supports all HART instruments using the universal DD (Device Description) library. It includes free lifetime DD database updates with no annual subscription fee."
        },
        {
            "question": "What is the difference between SK-660 and SK-660F?",
            "answer": "The SK-660F adds Foundation Fieldbus (FF) communication support in addition to HART. Both models share the same Android-based platform, IP67 rating, Zone 1 certification, and full HART functionality."
        },
        {
            "question": "Where can I buy HART Communicator in Chennai?",
            "answer": "You can buy the SK-660 HART Communicator directly from VISA Pvt. Ltd, located in Valasaravakkam, Chennai. Call +91 94453 50717 or visit hart475communicator.com to get a quote."
        },
    ]
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq["question"],
                "acceptedAnswer": {"@type": "Answer", "text": faq["answer"]}
            }
            for faq in faqs
        ]
    }
    return json.dumps(schema)


def _hart_products():
    return Product.objects.filter(
        is_active=True,
        category__division__slug=HART_DIVISION,
    ).select_related('category__division').prefetch_related('images')


def home(request):
    products = _hart_products()[:6]
    form = EnquiryForm()
    return render(request, 'hart_site/pages/home.html', {
        'products':   products,
        'form':       form,
        'meta_title': 'HART Communicator SK-660 Manufacturer India — Buy Online | VISA Pvt. Ltd',
        'meta_desc':  'Buy SK-660 HART Communicator — Intrinsically safe, IP67, Zone 1 rated. Android-based handheld HART communicator manufacturer in Chennai, India. Free DD updates. Get quote.',
        'org_schema': hart_organization_schema(),
        'faq_schema': _hart_faq_schema(),
    })


def products(request):
    products_qs = _hart_products()
    form = EnquiryForm()
    return render(request, 'hart_site/pages/products.html', {
        'products':   products_qs,
        'form':       form,
        'meta_title': 'HART Communicator Products — SK-660 & SK-660F | VISA Pvt. Ltd',
        'meta_desc':  'SK-660 and SK-660F HART Handheld Communicators. Android-based, IP67 rated, intrinsically safe. Chennai, India.',
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = _hart_products().exclude(id=product.id)[:3]
    form = EnquiryForm(initial={'product_name': product.name})
    base_url = f'{request.scheme}://{request.get_host()}'
    breadcrumbs = [
        ('Home',     f'{base_url}/'),
        ('Products', f'{base_url}/products/'),
        (product.name, None),
    ]
    return render(request, 'hart_site/pages/product_detail.html', {
        'product':     product,
        'related':     related,
        'form':        form,
        'images':      product.images.all(),
        'specs':       product.specifications,
        'apps_list':   product.get_applications_list(),
        'meta_title':  product.meta_title or f'{product.name} — HART Communicator Price India | VISA Pvt. Ltd',
        'meta_desc':   product.meta_desc or product.short_desc,
        'prod_schema': product_schema(product, request),
        'bc_schema':   breadcrumb_schema(breadcrumbs),
    })


def robots_txt(request):
    from django.http import HttpResponse
    content = "User-agent: *\nAllow: /\nSitemap: https://hart475communicator.com/sitemap.xml\n"
    return HttpResponse(content, content_type='text/plain')


def sitemap_xml(request):
    from django.http import HttpResponse
    from shared.models import Product
    products = Product.objects.filter(is_active=True, category__division__slug='hart-communicators')
    base = 'https://hart475communicator.com'
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in ['', 'products/', 'about/', 'contact/']:
        lines.append(f'  <url><loc>{base}/{url}</loc><changefreq>weekly</changefreq><priority>{"1.0" if url == "" else "0.8"}</priority></url>')
    for p in products:
        lines.append(f'  <url><loc>{base}/products/{p.slug}/</loc><changefreq>monthly</changefreq><priority>0.9</priority><lastmod>{p.updated_at.date()}</lastmod></url>')
    lines.append('</urlset>')
    return HttpResponse('\n'.join(lines), content_type='application/xml')


def about(request):
    strengths = [
        {'title': 'Intrinsically Safe',   'desc': 'SK-660 certified Ex ib IICT4 Gb — safe for Zone 1 hazardous areas in oil & gas, pharma, and chemical plants.'},
        {'title': 'Android-Based',        'desc': 'Modern Android 9.0 platform with large touchscreen. Easy to use, no proprietary hardware dependency.'},
        {'title': 'Free DD Library',      'desc': 'Complete HART Device Description library included. Free updates for life — no annual subscription fees.'},
        {'title': 'IP67 Rated',           'desc': 'Fully dust-tight and waterproof. Built for harsh field conditions including rain, dust, and humidity.'},
        {'title': 'Pan India Support',    'desc': 'Sales and technical support available across India. Fast delivery from our Chennai warehouse.'},
        {'title': 'Competitive Pricing',  'desc': 'Best price guarantee on SK-660 & SK-660F. Get a direct quote from manufacturer — no middleman markup.'},
    ]
    return render(request, 'hart_site/pages/about.html', {
        'strengths':  strengths,
        'meta_title': 'About VISA Pvt. Ltd — HART Communicator Manufacturer Chennai',
        'meta_desc':  'VISA Pvt. Ltd is a Chennai-based manufacturer of HART Communicators and industrial instruments. 20+ years experience. Authorised supplier across India.',
    })


def contact(request):
    form = EnquiryForm()
    return render(request, 'hart_site/pages/contact.html', {
        'form':       form,
        'meta_title': 'Contact — HART Communicator | VISA Pvt. Ltd Chennai',
        'meta_desc':  'Get a quote for SK-660 HART Communicator. Contact VISA Pvt. Ltd, Chennai. Phone: +91 94453 50717.',
    })


def _is_rate_limited(ip):
    from django.utils import timezone
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(hours=1)
    return Enquiry.objects.filter(ip_address=ip, created_at__gte=cutoff).count() >= 3


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
        enquiry            = form.save(commit=False)
        enquiry.source     = 'hart_site'
        enquiry.ip_address = ip
        product_slug       = request.POST.get('product_slug')
        if product_slug:
            try:
                enquiry.product = Product.objects.get(slug=product_slug)
            except Product.DoesNotExist:
                pass
        enquiry.save()
        send_enquiry_notification(enquiry)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Thank you! We will contact you within 24 hours.'})
        messages.success(request, 'Thank you! We will contact you within 24 hours.')
        return redirect('hart_home')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    messages.error(request, 'Please fill all required fields.')
    return redirect(request.META.get('HTTP_REFERER', '/'))
