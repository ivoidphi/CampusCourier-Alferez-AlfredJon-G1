from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path("", views.home_view, name="home"),
    path("register/", views.register_view, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard_redirect_view, name="dashboard_redirect"),
    path(
        "dashboard/customer/",
        views.customer_dashboard_view,
        name="customer_dashboard",
    ),
    path(
        "dashboard/courier/",
        views.courier_dashboard_view,
        name="courier_dashboard",
    ),
    path("dashboard/admin/", views.admin_dashboard_view, name="admin_dashboard"),
    path("profile/", views.profile_view, name="profile"),
]
