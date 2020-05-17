from django.contrib import admin

from .models import BuddyRequest, Profile


@admin.register(BuddyRequest)
class BuddyRequestAdmin(admin.ModelAdmin):
    fields = [
        "request_sent",
        "requestee",
        "requestor",
        "message",
        "status",
        "request_type",
    ]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    fields = ["user", "bio", "help_wanted", "can_help"]

