import os

import django_heroku
from .base import *

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG_MODE") == "true"

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "buddy_mentorship",
        "USER": "buddy_mentorship",
        "HOST": os.getenv("DATABASE_URL"),
    }
}

# will only work for one admin
ADMINS = [tuple(os.getenv("ADMINS").split(","))] if os.getenv("ADMINS") else []

django_heroku.settings(locals())

SECURE_SSL_REDIRECT = True
