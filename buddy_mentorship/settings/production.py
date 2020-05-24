import os

import django_heroku
from .base import *

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = False

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

django_heroku.settings(locals())
