"""shared/context_processors.py"""
from django.conf import settings
from .models import ProductDivision


def global_context(request):
    return {
        'divisions':       ProductDivision.objects.filter(is_active=True).prefetch_related(
                               'categories__products'
                           ),
        'whatsapp_number':    getattr(settings, 'WHATSAPP_NUMBER', '919445350717'),
        'sk660_brochure_url':  getattr(settings, 'SK660_BROCHURE_URL',  ''),
        'sk660f_brochure_url': getattr(settings, 'SK660F_BROCHURE_URL', ''),
        'company': {
            'name':    'Virtual Instrumentation & Software Applications Pvt. Ltd',
            'short':   'VISA Pvt. Ltd',
            'phone':   '+91 94453 50717',
            'email':   'support@visapvtltd.co.in',
            'address': '15/16/17 Vision Tower, Yogam Garden, Brindhavan Nagar, Valasaravakkam, Chennai — 600 087',
            'gst':     '33AABCV2361D1ZT',
            'cin':     'U72200TN1999PTC042478',
            'url':     'https://www.visapvtltd.co.in',
        },
    }
