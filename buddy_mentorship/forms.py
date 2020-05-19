from django import forms


class ProfileEditForm(forms.Form):
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
    bio = forms.CharField(widget=forms.Textarea)
    email = forms.EmailField()
    bio = forms.CharField()
    help_wanted = forms.BooleanField(required=False)
    can_help = forms.BooleanField(required=False)
