import urllib.request
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from shared.models import Product


def download_pdf(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if not product.pdf_brochure:
        raise Http404("No brochure available for this product.")

    cloudinary_url = product.pdf_brochure.url
    try:
        with urllib.request.urlopen(cloudinary_url) as response:
            pdf_bytes = response.read()
    except Exception:
        raise Http404("Brochure file could not be retrieved.")

    filename = f"{slug}_brochure.pdf"
    http_response = HttpResponse(pdf_bytes, content_type='application/pdf')
    http_response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return http_response
