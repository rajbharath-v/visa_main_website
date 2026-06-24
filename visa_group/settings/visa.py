"""visa_group/settings/visa.py — visapvtltd.net"""
import os
from .base import *
ALLOWED_HOSTS = [
    'visapvtltd.co.in',
    'www.visapvtltd.co.in',
    '163.128.113.15',
    'localhost',
    '127.0.0.1',
]
# Allow any domain set via env var (useful for custom Railway domains)
_extra_host = os.getenv('RAILWAY_PUBLIC_DOMAIN', '').strip()
if _extra_host:
    ALLOWED_HOSTS.append(_extra_host)

SITE_ID = 1
CURRENT_SITE = 'visa_main'

# Production security — Railway terminates SSL at proxy level
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # Railway handles this, not Django
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
