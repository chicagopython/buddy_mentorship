import uuid

from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)

    email = models.EmailField(_("email address"), unique=True)
    username = models.EmailField(null=True)  # field is required for python social auth
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

class Profile(models.Model):
    """
    A model for storing user profile information
    """
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    bio = models.CharField(max_length = 620)
    help_wanted = models.BooleanField(default = False)
    can_help = models.BooleanField(default = False)

    def __str__ (self):
        return self.bio
