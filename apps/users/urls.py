from django.urls import include, path
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.base import RedirectView
from . import views


urlpatterns = [
    path("login/", views.GithubRedirect.as_view(), name="login",),
    path(
        "logout/", LogoutView.as_view(template_name="users/logout.html"), name="logout",
    ),
    path("requests/<int:request_id>", views.request_detail, name="request_detail"),
    path("requests/", views.requests_list, name="requests"),
]
