"""
User serializers for authentication and user management.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, AuditLog


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details."""

    full_name = serializers.ReadOnlyField()
    display_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name", "display_name",
            "role", "phone", "department", "title", "license_number", "specialty",
            "is_active", "is_verified", "last_login", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "last_login", "created_at", "updated_at"]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users."""

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "email", "password", "password_confirm", "first_name", "last_name",
            "role", "phone", "department", "title", "license_number", "specialty"
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user details."""

    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "phone", "department",
            "title", "license_number", "specialty", "is_active"
        ]


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin updating user details including role."""

    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "role", "phone", "department",
            "title", "license_number", "specialty", "is_active", "is_verified"
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match"})
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for admin password reset."""

    new_password = serializers.CharField(required=True, validators=[validate_password])


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")

        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user self-registration."""

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["email", "password", "password_confirm", "first_name", "last_name", "phone"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        # New registrations get viewer role by default
        user = User(role="viewer", **validated_data)
        user.set_password(password)
        user.save()
        return user


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs."""

    user_email = serializers.CharField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id", "user", "user_email", "user_name", "action", "resource_type",
            "resource_id", "description", "ip_address", "user_agent", "timestamp", "metadata"
        ]
        read_only_fields = ["id", "timestamp"]


class UserPermissionsSerializer(serializers.Serializer):
    """Serializer for user permissions."""

    can_view_patients = serializers.BooleanField()
    can_edit_patients = serializers.BooleanField()
    can_view_clinical_data = serializers.BooleanField()
    can_edit_clinical_data = serializers.BooleanField()
    can_manage_devices = serializers.BooleanField()
    can_manage_users = serializers.BooleanField()
    can_view_analytics = serializers.BooleanField()
    can_manage_alerts = serializers.BooleanField()
