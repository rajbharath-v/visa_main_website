import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visa_group.settings.visa')
application = get_wsgi_application()
