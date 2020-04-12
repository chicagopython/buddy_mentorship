from .models import BuddyRequest
from django.forms import ModelForm


class BuddyRequestForm(ModelForm):
    class Meta:
        model = BuddyRequest
        fields = ("message",)