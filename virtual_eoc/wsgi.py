"""
WSGI config for virtual_eoc project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""
import sys
import os
path = '/var/www/ears_system'
if path not in sys.path:
    sys.path.append(path)
from django.core.wsgi import get_wsgi_application
#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "virtual_eoc.settings")

application = get_wsgi_application()
