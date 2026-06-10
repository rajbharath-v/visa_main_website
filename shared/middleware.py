"""shared/middleware.py — routes requests by domain"""


class SiteRouterMiddleware:
    """
    Detects which domain the request came from and
    sets request.current_site so views/templates can use it.
    """
    SITE_MAP = {
        'peristalticpump.in':     'pump_site',
        'www.peristalticpump.in': 'pump_site',
        'hartcommunicator.in':    'hart_site',
        'www.hartcommunicator.in':'hart_site',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        request.current_site = self.SITE_MAP.get(host, 'visa_main')
        response = self.get_response(request)
        return response
