from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    CurrentUserView,
    ChangePasswordView,
    UserListView,
    UserDetailView,
    ResetUserPasswordView,
    ToggleUserStatusView,
    AuditLogListView,
    UserStatsView,
)

urlpatterns = [
    # Authentication
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # Current user
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("me/change-password/", ChangePasswordView.as_view(), name="change-password"),

    # User management (admin)
    path("", UserListView.as_view(), name="user-list"),
    path("<int:user_id>/", UserDetailView.as_view(), name="user-detail"),
    path("<int:user_id>/reset-password/", ResetUserPasswordView.as_view(), name="reset-password"),
    path("<int:user_id>/toggle-status/", ToggleUserStatusView.as_view(), name="toggle-status"),

    # Audit logs (admin)
    path("audit-logs/", AuditLogListView.as_view(), name="audit-logs"),

    # Stats (admin)
    path("stats/", UserStatsView.as_view(), name="user-stats"),
]
