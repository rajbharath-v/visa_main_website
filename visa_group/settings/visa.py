"""visa_group/settings/visa.py — visapvtltd.net"""
from .base import *

ALLOWED_HOSTS = [
    'visapvtltd.net',
    'www.visapvtltd.net',
    'localhost',
    '127.0.0.1',
]

SITE_ID = 1
CURRENT_SITE = 'visa_main'

# Production security
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
