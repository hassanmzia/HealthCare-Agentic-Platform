from django.db import models
from patients.models import Patient


class Device(models.Model):
    """IoT Device model for vital sign monitoring equipment."""

    DEVICE_TYPES = [
        ("vital_monitor", "Vital Signs Monitor"),
        ("pulse_oximeter", "Pulse Oximeter"),
        ("bp_monitor", "Blood Pressure Monitor"),
        ("thermometer", "Thermometer"),
        ("ecg_monitor", "ECG Monitor"),
        ("glucose_monitor", "Glucose Monitor"),
        ("weight_scale", "Weight Scale"),
        ("multi_parameter", "Multi-Parameter Monitor"),
        ("wearable", "Wearable Device"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("maintenance", "Under Maintenance"),
        ("retired", "Retired"),
    ]

    # Identifiers
    device_id = models.CharField(max_length=100, unique=True, help_text="Unique device identifier")
    fhir_id = models.CharField(max_length=100, blank=True, null=True, help_text="FHIR Device resource ID")
    serial_number = models.CharField(max_length=100, blank=True)

    # Device Info
    name = models.CharField(max_length=200)
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPES, default="vital_monitor")
    manufacturer = models.CharField(max_length=200, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    firmware_version = models.CharField(max_length=50, blank=True)

    # Location
    facility = models.CharField(max_length=200, blank=True, help_text="Hospital/Clinic name")
    department = models.CharField(max_length=200, blank=True)
    room = models.CharField(max_length=50, blank=True)
    bed = models.CharField(max_length=50, blank=True)

    # Capabilities - what vitals can this device measure
    capabilities = models.JSONField(default=list, blank=True, help_text="List of vital signs this device can measure")

    # Configuration
    reading_interval_seconds = models.IntegerField(default=60, help_text="How often device sends readings")
    config = models.JSONField(default=dict, blank=True, help_text="Device-specific configuration")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    last_seen = models.DateTimeField(null=True, blank=True, help_text="Last time device sent data")
    battery_level = models.IntegerField(null=True, blank=True, help_text="Battery percentage 0-100")

    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Device"
        verbose_name_plural = "Devices"

    def __str__(self):
        return f"{self.name} ({self.device_id})"

    @property
    def current_assignment(self):
        """Get current active assignment if any."""
        return self.assignments.filter(is_active=True).first()

    @property
    def assigned_patient(self):
        """Get currently assigned patient if any."""
        assignment = self.current_assignment
        return assignment.patient if assignment else None


class DeviceAssignment(models.Model):
    """Tracks device-patient assignments over time."""

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="assignments")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="device_assignments")

    # Assignment period
    assigned_at = models.DateTimeField(auto_now_add=True)
    unassigned_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Assignment details
    assigned_by = models.CharField(max_length=200, blank=True, help_text="Staff member who made assignment")
    reason = models.TextField(blank=True, help_text="Reason for assignment")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-assigned_at"]
        verbose_name = "Device Assignment"
        verbose_name_plural = "Device Assignments"

    def __str__(self):
        status = "Active" if self.is_active else "Ended"
        return f"{self.device.name} -> {self.patient.full_name} ({status})"

    def save(self, *args, **kwargs):
        # If this is a new active assignment, deactivate other active assignments for this device
        if self.is_active and not self.pk:
            DeviceAssignment.objects.filter(device=self.device, is_active=True).update(
                is_active=False,
                unassigned_at=models.functions.Now()
            )
        super().save(*args, **kwargs)
