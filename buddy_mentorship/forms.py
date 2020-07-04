from django import forms
from dal import autocomplete
from .models import Experience


class ProfileEditForm(forms.Form):
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255, required=False)
    email = forms.EmailField()
    bio = forms.CharField(required=False, widget=forms.Textarea)
    help_wanted = forms.BooleanField(required=False)
    can_help = forms.BooleanField(required=False)


class SkillForm(forms.Form):
    skill = forms.CharField(max_length=50)
    level = forms.ChoiceField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])
    exp_type = forms.ChoiceField(choices=[(0, 0), (1, 1)])
