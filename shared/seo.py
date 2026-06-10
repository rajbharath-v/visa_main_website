"""shared/seo.py — JSON-LD schema builders"""
import json


def organization_schema():
    return json.dumps({
        "@context": "https://schema.org",
        "@type": ["Organization", "LocalBusiness"],
        "name": "Virtual Instrumentation & Software Applications Pvt. Ltd",
        "alternateName": "VISA Pvt. Ltd",
        "url": "https://www.visapvtltd.net",
        "logo": "https://www.visapvtltd.net/static/visa/img/logo.png",
        "telephone": "+917949093762",
        "email": "sales@visapvtltd.net",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "15/16/17 Vision Tower, Yogam Garden, Brindhavan Nagar",
            "addressLocality": "Valasaravakkam",
            "addressRegion": "Tamil Nadu",
            "postalCode": "600087",
            "addressCountry": "IN"
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": 13.04405,
            "longitude": 80.17880
        },
        "openingHours": "Mo-Sa 09:00-18:00",
        "priceRange": "₹₹",
        "sameAs": [
            "https://www.visapvtltd.net",
            "https://peristalticpump.in",
            "https://hartcommunicator.in"
        ]
    }, indent=2)


def website_schema():
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "VISA Pvt. Ltd",
        "url": "https://www.visapvtltd.net",
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": "https://www.visapvtltd.net/products/?q={search_term_string}"
            },
            "query-input": "required name=search_term_string"
        }
    }, indent=2)


def product_schema(product, request):
    base_url = f'{request.scheme}://{request.get_host()}'
    img_url  = ''
    if product.primary_image:
        img_url = f'{base_url}{product.primary_image.image.url}'

    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "description": product.description[:500],
        "brand": {
            "@type": "Brand",
            "name": "VISA Pvt. Ltd"
        },
        "manufacturer": {
            "@type": "Organization",
            "name": "Virtual Instrumentation & Software Applications Pvt. Ltd",
            "url": "https://www.visapvtltd.net"
        },
        "offers": {
            "@type": "Offer",
            "priceCurrency": "INR",
            "availability": "https://schema.org/InStock"
                            if product.stock_status == 'available'
                            else "https://schema.org/PreOrder",
            "seller": {
                "@type": "Organization",
                "name": "VISA Pvt. Ltd"
            }
        }
    }
    if img_url:
        schema['image'] = img_url
    return json.dumps(schema, indent=2)


def breadcrumb_schema(items):
    """items = [('Home', 'https://...'), ('Category', 'https://...'), ('Product', None)]"""
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": name,
                **({"item": url} if url else {})
            }
            for i, (name, url) in enumerate(items)
        ]
    }, indent=2)
