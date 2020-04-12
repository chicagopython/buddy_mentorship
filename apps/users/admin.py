from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import UserCreationForm, UserChangeForm
from .models import User, Profile


class UserAdmin(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User
    list_display = ("email", "is_staff", "is_active", "uuid")
    list_filter = ("email", "is_staff", "is_active")
    fieldsets = ((None, {"fields": ("email", "password", "first_name", "last_name")}), ("Permissions", {"fields": ("is_staff", "is_active")}))
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "first_name", "last_name", "is_staff", "is_active")}),
    )
    search_fields = ("email",)
    ordering = ("email",)


admin.site.register(User, UserAdmin)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    fields = ['user', 'bio', 'help_wanted', 'can_help']