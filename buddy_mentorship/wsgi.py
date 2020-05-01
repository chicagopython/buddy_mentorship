"""
WSGI config for buddy_mentorship project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from dotenv import load_dotenv

load_dotenv(override=True, verbose=True)

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "buddy_mentorship.settings")

application = get_wsgi_application()
