from django.contrib import admin

from .models import BuddyRequest, Profile, Skill, Experience


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
    fields = ["user", "bio"]


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    fields = ["skill", "display_name"]


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    fields = ["profile", "skill", "level", "exp_type"]
