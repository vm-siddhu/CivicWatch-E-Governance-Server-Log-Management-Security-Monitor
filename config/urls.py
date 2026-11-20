from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from logs import views as log_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/register/", log_views.register, name="register"),
    path("", include("logs.urls")),
    path("api/", include("logs.api_urls")),
]
