"""
User views for authentication and user management.
"""

from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import User, AuditLog
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    AdminUserUpdateSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    AuditLogSerializer,
    UserPermissionsSerializer,
)
from .permissions import IsAdmin, CanManageUsers


def get_client_ip(request):
    """Get client IP from request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


def log_action(user, action, resource_type, resource_id="", description="", request=None, metadata=None):
    """Create an audit log entry."""
    AuditLog.objects.create(
        user=user,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        description=description,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500] if request else "",
        metadata=metadata or {},
    )


class RegisterView(APIView):
    """User self-registration endpoint."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            log_action(user, "create", "User", user.id, "User registered", request)

            # Generate tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """User login endpoint."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]

            # Update last login info
            user.last_login = timezone.now()
            user.last_login_ip = get_client_ip(request)
            user.save(update_fields=["last_login", "last_login_ip"])

            # Generate tokens
            refresh = RefreshToken.for_user(user)

            log_action(user, "login", "User", user.id, "User logged in", request)

            return Response({
                "user": UserSerializer(user).data,
                "permissions": {
                    "can_view_patients": user.can_view_patients(),
                    "can_edit_patients": user.can_edit_patients(),
                    "can_view_clinical_data": user.can_view_clinical_data(),
                    "can_edit_clinical_data": user.can_edit_clinical_data(),
                    "can_manage_devices": user.can_manage_devices(),
                    "can_manage_users": user.can_manage_users(),
                    "can_view_analytics": user.can_view_analytics(),
                    "can_manage_alerts": user.can_manage_alerts(),
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """User logout endpoint - blacklists the refresh token."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            log_action(request.user, "logout", "User", request.user.id, "User logged out", request)

            return Response({"message": "Successfully logged out"})
        except Exception:
            return Response({"message": "Logged out"})


class CurrentUserView(APIView):
    """Get current user profile and permissions."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "user": UserSerializer(user).data,
            "permissions": {
                "can_view_patients": user.can_view_patients(),
                "can_edit_patients": user.can_edit_patients(),
                "can_view_clinical_data": user.can_view_clinical_data(),
                "can_edit_clinical_data": user.can_edit_clinical_data(),
                "can_manage_devices": user.can_manage_devices(),
                "can_manage_users": user.can_manage_users(),
                "can_view_analytics": user.can_view_analytics(),
                "can_manage_alerts": user.can_manage_alerts(),
            }
        })

    def put(self, request):
        """Update current user profile."""
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            log_action(request.user, "update", "User", request.user.id, "User updated profile", request)
            return Response(UserSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Change password for current user."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user

            if not user.check_password(serializer.validated_data["current_password"]):
                return Response(
                    {"current_password": "Incorrect password"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(serializer.validated_data["new_password"])
            user.save()

            log_action(user, "update", "User", user.id, "User changed password", request)

            return Response({"message": "Password changed successfully"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Admin User Management Views

class UserListView(APIView):
    """List and create users (admin only)."""

    permission_classes = [IsAuthenticated, CanManageUsers]

    def get(self, request):
        """List all users with filtering."""
        users = User.objects.all()

        # Filtering
        search = request.query_params.get("search")
        if search:
            users = users.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        role = request.query_params.get("role")
        if role:
            users = users.filter(role=role)

        department = request.query_params.get("department")
        if department:
            users = users.filter(department=department)

        is_active = request.query_params.get("is_active")
        if is_active is not None:
            users = users.filter(is_active=is_active.lower() == "true")

        # Pagination
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))
        total = users.count()
        users = users[offset:offset + limit]

        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": UserSerializer(users, many=True).data
        })

    def post(self, request):
        """Create a new user."""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            log_action(request.user, "create", "User", user.id, f"Admin created user {user.email}", request)
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    """Get, update, delete a specific user (admin only)."""

    permission_classes = [IsAuthenticated, CanManageUsers]

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    def get(self, request, user_id):
        user = self.get_user(user_id)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserSerializer(user).data)

    def put(self, request, user_id):
        user = self.get_user(user_id)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            log_action(request.user, "update", "User", user.id, f"Admin updated user {user.email}", request)
            return Response(UserSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id):
        user = self.get_user(user_id)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if user == request.user:
            return Response(
                {"error": "Cannot delete your own account"},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = user.email
        user_id_str = str(user.id)
        user.delete()

        log_action(request.user, "delete", "User", user_id_str, f"Admin deleted user {email}", request)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ResetUserPasswordView(APIView):
    """Admin reset user password."""

    permission_classes = [IsAuthenticated, CanManageUsers]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data["new_password"])
            user.save()

            log_action(request.user, "update", "User", user.id, f"Admin reset password for {user.email}", request)

            return Response({"message": "Password reset successfully"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ToggleUserStatusView(APIView):
    """Enable/disable a user account."""

    permission_classes = [IsAuthenticated, CanManageUsers]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if user == request.user:
            return Response(
                {"error": "Cannot disable your own account"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])

        action_desc = "enabled" if user.is_active else "disabled"
        log_action(request.user, "update", "User", user.id, f"Admin {action_desc} user {user.email}", request)

        return Response({
            "message": f"User {action_desc} successfully",
            "is_active": user.is_active
        })


class AuditLogListView(APIView):
    """List audit logs (admin only)."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        logs = AuditLog.objects.all()

        # Filtering
        user_id = request.query_params.get("user_id")
        if user_id:
            logs = logs.filter(user_id=user_id)

        action = request.query_params.get("action")
        if action:
            logs = logs.filter(action=action)

        resource_type = request.query_params.get("resource_type")
        if resource_type:
            logs = logs.filter(resource_type=resource_type)

        start_date = request.query_params.get("start_date")
        if start_date:
            logs = logs.filter(timestamp__date__gte=start_date)

        end_date = request.query_params.get("end_date")
        if end_date:
            logs = logs.filter(timestamp__date__lte=end_date)

        # Pagination
        limit = int(request.query_params.get("limit", 100))
        offset = int(request.query_params.get("offset", 0))
        total = logs.count()
        logs = logs[offset:offset + limit]

        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": AuditLogSerializer(logs, many=True).data
        })


class UserStatsView(APIView):
    """Get user statistics (admin only)."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()

        # By role
        by_role = {}
        for role, _ in User.ROLE_CHOICES:
            by_role[role] = User.objects.filter(role=role).count()

        # By department
        by_department = {}
        for dept, _ in User.DEPARTMENT_CHOICES:
            count = User.objects.filter(department=dept).count()
            if count > 0:
                by_department[dept] = count

        # Recent logins (last 24 hours)
        from datetime import timedelta
        recent_logins = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(hours=24)
        ).count()

        return Response({
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "by_role": by_role,
            "by_department": by_department,
            "recent_logins_24h": recent_logins,
        })
