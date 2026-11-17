from django.urls import path

from . import views

urlpatterns = [
    path("auth/csrf/", views.csrf_view, name="csrf"),
    path("auth/register/", views.register_view, name="register"),
    path("auth/login/", views.login_view, name="login"),
    path("auth/logout/", views.logout_view, name="logout"),
    path("auth/me/", views.me_view, name="me"),
]
