"""visa_group/settings/visa.py — visapvtltd.net"""
import os
from .base import *

ALLOWED_HOSTS = [
    'visapvtltd.net',
    'www.visapvtltd.net',
    'visapvtltd.co.in',
    'www.visapvtltd.co.in',
    'hartcommunicator.in',
    'www.hartcommunicator.in',
    'hart475communicator.com',
    'www.hart475communicator.com',
    'peristalticpump.in',
    'www.peristalticpump.in',
    'peristalticspump.com',
    'www.peristalticspump.com',
    '163.128.113.15',
    'localhost',
    '127.0.0.1',
]

# Allow VPS IP override via env var
_vps_ip = os.getenv('VPS_IP', '').strip()
if _vps_ip:
    ALLOWED_HOSTS.append(_vps_ip)

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
