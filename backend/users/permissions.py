"""
Role-based permission classes for the health platform.
"""

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Permission for admin-only access."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


class IsAdminOrDoctor(BasePermission):
    """Permission for admin or doctor access."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["admin", "doctor"]


class IsClinicalStaff(BasePermission):
    """Permission for clinical staff (admin, doctor, nurse)."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["admin", "doctor", "nurse"]


class CanViewPatients(BasePermission):
    """Permission to view patient data."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_view_patients()


class CanEditPatients(BasePermission):
    """Permission to edit patient data."""

    def has_permission(self, request, view):
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return request.user.is_authenticated and request.user.can_view_patients()
        return request.user.is_authenticated and request.user.can_edit_patients()


class CanViewClinicalData(BasePermission):
    """Permission to view clinical data."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_view_clinical_data()


class CanEditClinicalData(BasePermission):
    """Permission to edit clinical data."""

    def has_permission(self, request, view):
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return request.user.is_authenticated and request.user.can_view_clinical_data()
        return request.user.is_authenticated and request.user.can_edit_clinical_data()


class CanManageDevices(BasePermission):
    """Permission to manage devices."""

    def has_permission(self, request, view):
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.can_manage_devices()


class CanManageUsers(BasePermission):
    """Permission to manage users."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_manage_users()


class CanViewAnalytics(BasePermission):
    """Permission to view analytics."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_view_analytics()


class CanManageAlerts(BasePermission):
    """Permission to manage alerts."""

    def has_permission(self, request, view):
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.can_manage_alerts()


class IsOwnerOrAdmin(BasePermission):
    """Permission for owner of resource or admin."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        # Check if object has user field
        if hasattr(obj, "user"):
            return obj.user == request.user
        # Check if object is the user themselves
        if hasattr(obj, "email"):
            return obj == request.user
        return False
