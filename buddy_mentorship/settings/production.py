import os

import django_heroku
from .base import *

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG_MODE") == "true"

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# will only work for one admin
ADMINS = [tuple(os.getenv("ADMINS").split(","))] if os.getenv("ADMINS") else []

django_heroku.settings(locals())

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
