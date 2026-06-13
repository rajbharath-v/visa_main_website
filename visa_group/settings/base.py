"""
visa_group/settings/base.py
Shared settings for all 3 VISA websites
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'cloudinary',
    # VISA apps
    'shared',
    'visa_main',
    'pump_site',
    'hart_site',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom domain router
    'shared.middleware.SiteRouterMiddleware',
]

ROOT_URLCONF = 'visa_group.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shared.context_processors.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'visa_group.wsgi.application'

# Database — supports both DATABASE_URL (Railway) and individual DB_* vars
import urllib.parse

_database_url = os.getenv('DATABASE_URL', '').strip()
if _database_url:
    _url = urllib.parse.urlparse(_database_url)
    DATABASES = {
        'default': {
            'ENGINE':   'django.db.backends.postgresql',
            'NAME':     _url.path.lstrip('/'),
            'USER':     _url.username,
            'PASSWORD': _url.password,
            'HOST':     _url.hostname,
            'PORT':     str(_url.port or 5432),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE':   'django.db.backends.postgresql',
            'NAME':     os.getenv('DB_NAME', 'visa_db'),
            'USER':     os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
            'HOST':     os.getenv('DB_HOST', 'localhost').strip(),
            'PORT':     os.getenv('DB_PORT', '5432').strip(),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cloudinary — permanent image storage (uses cloudinary SDK directly, Django 5+ compatible)
import cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'dyhaocbiu'),
    api_key=os.getenv('CLOUDINARY_API_KEY', '595497222666167'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', ''),
    secure=True,
)

STORAGES = {
    'default': {
        'BACKEND': 'cloudinary.storage.MediaCloudinaryStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email — Gmail SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@visapvtltd.net')
ENQUIRY_EMAIL = os.getenv('ENQUIRY_EMAIL', 'sales@visapvtltd.net')

# WhatsApp
WHATSAPP_NUMBER = os.getenv('WHATSAPP_NUMBER', '917949093762')

# ── JAZZMIN ──────────────────────────────────────────────────────────────────
JAZZMIN_SETTINGS = {
    "site_title":        "VISA Admin",
    "site_header":       "VISA Pvt. Ltd",
    "site_brand":        "VISA",
    "site_logo":         "visa/img/logo.png",
    "site_logo_classes": "img-circle elevation-3",
    "login_logo":        "visa/img/logo.png",
    "login_logo_dark":   "visa/img/logo.png",
    "site_icon":         "visa/img/logo.png",
    "welcome_sign":      "Welcome to VISA Admin Panel",
    "copyright":         "VISA Pvt. Ltd, Chennai",
    "search_model":      ["shared.Enquiry", "shared.Product"],
    "user_avatar":       None,
    "topmenu_links": [
        {"name": "Analytics",   "url": "/admin/analytics/", "permissions": ["auth.view_user"], "icon": "fas fa-chart-bar"},
        {"name": "View Site",   "url": "/",  "new_window": True, "icon": "fas fa-external-link-alt"},
        {"model": "shared.Enquiry"},
    ],
    "usermenu_links": [
        {"name": "View Site", "url": "/", "new_window": True},
    ],
    "show_sidebar":           True,
    "navigation_expanded":    True,
    "hide_apps":              [],
    "hide_models":            [],
    "order_with_respect_to":  [
        "shared", "shared.Enquiry", "shared.Product",
        "shared.ProductCategory", "shared.ProductDivision", "shared.BlogPost",
        "auth",
    ],
    "icons": {
        "auth":                    "fas fa-users-cog",
        "auth.user":               "fas fa-user",
        "auth.Group":              "fas fa-users",
        "shared.Enquiry":          "fas fa-envelope-open-text",
        "shared.Product":          "fas fa-boxes",
        "shared.ProductCategory":  "fas fa-folder-open",
        "shared.ProductDivision":  "fas fa-layer-group",
        "shared.ProductImage":     "fas fa-images",
        "shared.BlogPost":         "fas fa-blog",
    },
    "default_icon_parents":  "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active":  False,
    "show_ui_builder":       False,
    "changeform_format":     "horizontal_tabs",
    "changeform_format_overrides": {"auth.user": "collapsible"},
    "language_chooser":      False,
    "custom_css":            "visa/css/admin_custom.css",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text":          False,
    "footer_small_text":          False,
    "body_small_text":            False,
    "brand_small_text":           False,
    "brand_colour":               "navbar-primary",
    "accent":                     "accent-primary",
    "navbar":                     "navbar-dark",
    "no_navbar_border":           True,
    "navbar_fixed":               True,
    "layout_boxed":               False,
    "footer_fixed":               False,
    "sidebar_fixed":              True,
    "sidebar":                    "sidebar-dark-primary",
    "sidebar_nav_small_text":     False,
    "sidebar_disable_expand":     False,
    "sidebar_nav_child_indent":   True,
    "sidebar_nav_compact_style":  True,
    "sidebar_nav_legacy_style":   False,
    "sidebar_nav_flat_style":     False,
    "theme":                      "default",
    "default_theme_mode":         "light",
    "button_classes": {
        "primary":   "btn-primary",
        "secondary": "btn-secondary",
        "info":      "btn-info",
        "warning":   "btn-warning",
        "danger":    "btn-danger",
        "success":   "btn-success",
    },
}
