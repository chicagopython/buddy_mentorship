from django.contrib import admin

from .models import BuddyRequest

@admin.register(BuddyRequest)
class BuddyRequestAdmin(admin.ModelAdmin):
    fields = ['requestSent', 'requestee', 'requestor', 'message']