"""visa_group/settings/visa.py — visapvtltd.net"""
import os
from .base import *

ALLOWED_HOSTS = [
    'visapvtltd.net',
    'www.visapvtltd.net',
    'localhost',
    '127.0.0.1',
    'web-production-55759.up.railway.app',
    '.railway.app',
]

# Allow any domain set via env var (useful for custom Railway domains)
_extra_host = os.getenv('RAILWAY_PUBLIC_DOMAIN', '').strip()
if _extra_host:
    ALLOWED_HOSTS.append(_extra_host)

SITE_ID = 1
CURRENT_SITE = 'visa_main'

# Production security
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
