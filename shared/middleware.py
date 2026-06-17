"""shared/middleware.py — routes requests by domain"""


class SiteRouterMiddleware:
    SITE_MAP = {
        'peristalticpump.in':      'pump_site',
        'www.peristalticpump.in':  'pump_site',
        'hartcommunicator.in':     'hart_site',
        'www.hartcommunicator.in': 'hart_site',
        'localhost':               'hart_site',  # LOCAL TESTING ONLY
        '127.0.0.1':              'hart_site',  # LOCAL TESTING ONLY
    }
    URLCONF_MAP = {
        'pump_site': 'pump_site.urls',
        'hart_site': 'hart_site.urls',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        request.current_site = self.SITE_MAP.get(host, 'visa_main')
        if request.current_site in self.URLCONF_MAP:
            request.urlconf = self.URLCONF_MAP[request.current_site]
        response = self.get_response(request)
        return response
