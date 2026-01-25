"""
User models with role-based access control.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Extended User model with roles and profile information."""

    ROLE_CHOICES = [
        ("admin", "Administrator"),
        ("doctor", "Doctor/Physician"),
        ("nurse", "Nurse"),
        ("technician", "Lab Technician"),
        ("receptionist", "Receptionist"),
        ("viewer", "Read-Only Viewer"),
    ]

    DEPARTMENT_CHOICES = [
        ("general", "General Medicine"),
        ("cardiology", "Cardiology"),
        ("neurology", "Neurology"),
        ("pediatrics", "Pediatrics"),
        ("oncology", "Oncology"),
        ("emergency", "Emergency"),
        ("icu", "Intensive Care Unit"),
        ("surgery", "Surgery"),
        ("radiology", "Radiology"),
        ("laboratory", "Laboratory"),
        ("pharmacy", "Pharmacy"),
        ("other", "Other"),
    ]

    # Override username to make email the primary identifier
    username = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)

    # Role and permissions
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="viewer")

    # Profile information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, blank=True)
    title = models.CharField(max_length=100, blank=True, help_text="Professional title (e.g., MD, RN)")
    license_number = models.CharField(max_length=50, blank=True, help_text="Medical license number")
    specialty = models.CharField(max_length=100, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Settings
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def display_name(self):
        if self.title:
            return f"{self.title} {self.full_name}"
        return self.full_name

    def has_role(self, *roles):
        """Check if user has any of the specified roles."""
        return self.role in roles

    def can_view_patients(self):
        return self.role in ["admin", "doctor", "nurse", "technician", "receptionist", "viewer"]

    def can_edit_patients(self):
        return self.role in ["admin", "doctor", "nurse", "receptionist"]

    def can_view_clinical_data(self):
        return self.role in ["admin", "doctor", "nurse", "technician"]

    def can_edit_clinical_data(self):
        return self.role in ["admin", "doctor", "nurse"]

    def can_manage_devices(self):
        return self.role in ["admin", "technician"]

    def can_manage_users(self):
        return self.role == "admin"

    def can_view_analytics(self):
        return self.role in ["admin", "doctor", "nurse"]

    def can_manage_alerts(self):
        return self.role in ["admin", "doctor", "nurse"]


class AuditLog(models.Model):
    """Audit log for tracking user actions."""

    ACTION_CHOICES = [
        ("login", "Login"),
        ("logout", "Logout"),
        ("create", "Create"),
        ("read", "Read"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("export", "Export"),
        ("acknowledge", "Acknowledge Alert"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="audit_logs")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50, help_text="Type of resource (e.g., Patient, Device)")
    resource_id = models.CharField(max_length=100, blank=True, help_text="ID of the affected resource")
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["action", "timestamp"]),
            models.Index(fields=["resource_type", "resource_id"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.resource_type} - {self.timestamp}"
