"""pump_site/views.py — peristalticpump.in"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from shared.models import Product, Enquiry
from shared.forms import EnquiryForm
from shared.emails import send_enquiry_notification

PUMP_DIVISION = 'fluid-handling'


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
        'meta_title': 'Peristaltic Pump Manufacturer in Chennai — VISA Pvt. Ltd',
        'meta_desc':  'Industrial Peristaltic Pumps by VISA Pvt. Ltd, Chennai. LabQ & Low-Cost models. Precise flow control for pharma, chemical, lab & food industries. Get best quote.',
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
    return render(request, 'pump_site/pages/product_detail.html', {
        'product':    product,
        'related':    related,
        'form':       form,
        'images':     product.images.all(),
        'specs':      product.specifications,
        'apps_list':  product.get_applications_list(),
        'meta_title': product.meta_title or f'{product.name} — Peristaltic Pump | VISA Pvt. Ltd Chennai',
        'meta_desc':  product.meta_desc or product.short_desc,
    })


def robots_txt(request):
    from django.http import HttpResponse
    content = "User-agent: *\nAllow: /\nSitemap: https://peristalticpump.in/sitemap.xml\n"
    return HttpResponse(content, content_type='text/plain')


def sitemap_xml(request):
    from django.http import HttpResponse
    products = _pump_products()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in ['', 'products/', 'about/', 'contact/']:
        lines.append(f'  <url><loc>https://peristalticpump.in/{url}</loc><changefreq>weekly</changefreq><priority>{"1.0" if url == "" else "0.8"}</priority></url>')
    for p in products:
        lines.append(f'  <url><loc>https://peristalticpump.in/products/{p.slug}/</loc><changefreq>monthly</changefreq><priority>0.9</priority></url>')
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
        'meta_desc':  'Get a quote for peristaltic pumps from VISA Pvt. Ltd, Chennai. Phone: +91 79490 93762. Email: sales@visapvtltd.net.',
    })


@require_POST
def submit_enquiry(request):
    form = EnquiryForm(request.POST)
    if form.is_valid():
        enquiry            = form.save(commit=False)
        enquiry.source     = 'pump_site'
        enquiry.ip_address = request.META.get('REMOTE_ADDR')
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
