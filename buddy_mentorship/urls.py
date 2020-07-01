"""buddy_mentorship URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("admin/", admin.site.urls),
    path("", include("apps.users.urls")),
    path("profile/", views.profile, name="your_profile"),
    path("profile/<int:profile_id>", views.profile, name="profile"),
    path("profile_edit/", views.ProfileEdit.as_view(), name="edit_profile"),
    path("edit_skill/<int:pk>", views.UpdateExperience.as_view(), name="edit_skill",),
    path(
        "delete_skill/<int:pk>", views.DeleteExperience.as_view(), name="delete_skill",
    ),
    path("skill", views.skill_search, name="skill_search"),
    path("add_skill/<int:exp_type>", views.AddSkill.as_view(), name="add_skill"),
    path("send_request/<uuid:uuid>", views.send_request, name="send_request"),
    path(
        "update_request/<int:buddy_request_id>",
        views.update_request,
        name="update_request",
    ),
    path("social/", include("social_django.urls", namespace="social")),
    path("search/", views.Search.as_view(), name="search"),
]
