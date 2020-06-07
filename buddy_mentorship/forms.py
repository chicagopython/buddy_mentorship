from django import forms
from dal import autocomplete


class ProfileEditForm(forms.Form):
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
    bio = forms.CharField(widget=forms.Textarea)
    email = forms.EmailField()
    bio = forms.CharField()
    help_wanted = forms.BooleanField(required=False)
    can_help = forms.BooleanField(required=False)


class SkillForm(forms.Form):
    skill = forms.CharField(max_length=30)
    level = forms.ChoiceField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])
    can_help = forms.BooleanField(required=False)
    help_wanted = forms.BooleanField(required=False)
