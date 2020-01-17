from django.urls import include, path
from django.contrib.auth import views


urlpatterns = ["login/", views.LoginView.as_view(template_name="users/login.html")]
