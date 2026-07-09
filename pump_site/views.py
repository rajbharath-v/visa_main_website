"""pump_site/views.py — peristalticspump.com"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from shared.models import Product, Enquiry
from shared.forms import EnquiryForm
from shared.emails import send_enquiry_notification
from shared.seo import pump_organization_schema, product_schema, breadcrumb_schema

PUMP_DIVISION = 'fluid-handling'


def _pump_faq_schema():
    import json
    faqs = [
        {
            "question": "What is a peristaltic pump?",
            "answer": "A peristaltic pump moves fluid by compressing a flexible tube using rotating rollers. The fluid only contacts the tube — making it ideal for sterile, corrosive, or abrasive fluids in pharma, chemical, and food industries."
        },
        {
            "question": "What is the price of a peristaltic pump in India?",
            "answer": "Peristaltic pump prices in India vary by model and flow rate. VISA Pvt. Ltd offers competitive factory-direct pricing for LabQ and industrial peristaltic pumps. Contact us at +91 94453 50717 for a quote."
        },
        {
            "question": "What industries use peristaltic pumps?",
            "answer": "Peristaltic pumps are widely used in pharmaceutical manufacturing, chemical dosing, food & beverage processing, water treatment, laboratory research, and environmental monitoring."
        },
        {
            "question": "What flow rates do VISA peristaltic pumps support?",
            "answer": "VISA peristaltic pumps support a wide range of flow rates from micro-dosing in laboratory applications to high-volume industrial transfer. Contact us for specific flow rate requirements."
        },
        {
            "question": "Are VISA peristaltic pumps suitable for corrosive chemicals?",
            "answer": "Yes. VISA peristaltic pumps are available with Silicone, PharMed, Norprene, and Viton tubing options to handle a wide range of corrosive, abrasive, and high-purity fluids."
        },
        {
            "question": "Where can I buy peristaltic pumps in Chennai?",
            "answer": "You can buy peristaltic pumps directly from VISA Pvt. Ltd, Valasaravakkam, Chennai. Visit peristalticspump.com or call +91 94453 50717 for pricing and availability."
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


def _pump_products():
    return Product.objects.filter(
        is_active=True,
        category__division__slug=PUMP_DIVISION,
    ).select_related('category__division').prefetch_related('images')


def home(request):
    products = _pump_products()[:6]
    form = EnquiryForm()
    return render(request, 'pump_site/pages/home.html', {
        'products':        products,
        'form':            form,
        'apps_list_home':  ['Pharmaceutical', 'Chemical Industry', 'Food & Beverage', 'Water Treatment', 'Laboratory', 'Environmental'],
        'badges':          ['ISO Certified', 'Made in India', '20+ Years', 'Pharma Grade', 'Easy Maintenance'],
        'meta_title':  'Peristaltic Pump Manufacturer in India — Buy Online | VISA Pvt. Ltd Chennai',
        'meta_desc':   'Buy Peristaltic Pumps from VISA Pvt. Ltd, Chennai. LabQ & Industrial models. Pharma grade, chemical resistant. Best price. Free quote — call +91 94453 50717.',
        'org_schema':  pump_organization_schema(),
        'faq_schema':  _pump_faq_schema(),
    })


def products(request):
    products_qs = _pump_products()
    return render(request, 'pump_site/pages/products.html', {
        'products':   products_qs,
        'meta_title': 'Peristaltic Pump Products — LabQ & Industrial Models | VISA Pvt. Ltd',
        'meta_desc':  'Browse our peristaltic pump range. LabQ precision pump and Low-Cost industrial pump. Wide flow range, chemical resistant, easy maintenance. VISA Pvt. Ltd Chennai.',
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = _pump_products().exclude(id=product.id)[:3]
    form = EnquiryForm(initial={'product_name': product.name})
    base_url = f'{request.scheme}://{request.get_host()}'
    breadcrumbs = [
        ('Home',     f'{base_url}/'),
        ('Products', f'{base_url}/products/'),
        (product.name, None),
    ]
    return render(request, 'pump_site/pages/product_detail.html', {
        'product':     product,
        'related':     related,
        'form':        form,
        'images':      product.images.all(),
        'specs':       product.specifications,
        'apps_list':   product.get_applications_list(),
        'meta_title':  product.meta_title or f'{product.name} — Peristaltic Pump Price India | VISA Pvt. Ltd',
        'meta_desc':   product.meta_desc or product.short_desc,
        'prod_schema': product_schema(product, request),
        'bc_schema':   breadcrumb_schema(breadcrumbs),
    })


def robots_txt(request):
    from django.http import HttpResponse
    content = "User-agent: *\nAllow: /\nSitemap: https://peristalticspump.com/sitemap.xml\n"
    return HttpResponse(content, content_type='text/plain')


def sitemap_xml(request):
    from django.http import HttpResponse
    products = _pump_products()
    base = 'https://peristalticspump.com'
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
        {'title': 'In-house Manufacturing', 'desc': 'All pumps designed and manufactured at our Chennai facility — quality control at every stage.'},
        {'title': 'Quality Assured',        'desc': 'Rigorous testing before dispatch. Strict protocols for dimensional accuracy and performance.'},
        {'title': 'Technical Support',      'desc': 'Engineers provide pre-sales consultation, installation guidance, and after-sales service across India.'},
        {'title': 'Chemical Compatibility', 'desc': 'Silicone, PharMed, Norprene, Viton tubing options — matched to your fluid type and chemical requirements.'},
        {'title': 'Custom Solutions',       'desc': 'From micro-dosing to bulk transfer, we engineer pumps to your specific flow rate and application.'},
        {'title': 'Fast Delivery',          'desc': 'Pan India delivery. Standard models from stock. Custom orders fulfilled in 2–4 weeks.'},
    ]
    return render(request, 'pump_site/pages/about.html', {
        'strengths':  strengths,
        'meta_title': 'About VISA Pvt. Ltd — Peristaltic Pump Manufacturer Chennai',
        'meta_desc':  'VISA Pvt. Ltd is a Chennai-based manufacturer of industrial peristaltic pumps, HART communicators and control instruments. ISO certified, 20+ years experience.',
    })


def contact(request):
    form = EnquiryForm()
    return render(request, 'pump_site/pages/contact.html', {
        'form':       form,
        'meta_title': 'Contact — Peristaltic Pump Enquiry | VISA Pvt. Ltd Chennai',
        'meta_desc':  'Get a quote for peristaltic pumps from VISA Pvt. Ltd, Chennai. Phone: +91 94453 50717. Email: support@visapvtltd.co.in.',
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
        enquiry.source     = 'pump_site'
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
        return redirect('pump_home')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    messages.error(request, 'Please fill all required fields.')
    return redirect(request.META.get('HTTP_REFERER', '/'))
