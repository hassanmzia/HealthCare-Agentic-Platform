from django.db import models
from patients.models import Patient
from devices.models import Device


class AlertRule(models.Model):
    """Configurable alert rules for vital sign thresholds."""

    VITAL_TYPES = [
        ("heart_rate", "Heart Rate"),
        ("blood_pressure_systolic", "Blood Pressure (Systolic)"),
        ("blood_pressure_diastolic", "Blood Pressure (Diastolic)"),
        ("oxygen_saturation", "Oxygen Saturation (SpO2)"),
        ("temperature", "Temperature"),
        ("respiratory_rate", "Respiratory Rate"),
        ("glucose", "Blood Glucose"),
    ]

    CONDITION_TYPES = [
        ("gt", "Greater Than"),
        ("gte", "Greater Than or Equal"),
        ("lt", "Less Than"),
        ("lte", "Less Than or Equal"),
        ("eq", "Equal To"),
        ("range_outside", "Outside Range"),
    ]

    SEVERITY_CHOICES = [
        ("info", "Information"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    vital_type = models.CharField(max_length=50, choices=VITAL_TYPES)
    condition = models.CharField(max_length=20, choices=CONDITION_TYPES, default="gt")
    threshold_value = models.DecimalField(max_digits=10, decimal_places=2)
    threshold_value_high = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                                help_text="Upper bound for range_outside condition")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="warning")

    # Scope - can be global or patient-specific
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True,
                                related_name="alert_rules", help_text="Leave blank for global rule")

    # Rule settings
    is_active = models.BooleanField(default=True)
    cooldown_minutes = models.IntegerField(default=15, help_text="Minutes before re-alerting for same condition")
    auto_acknowledge_minutes = models.IntegerField(default=0, help_text="Auto-acknowledge after N minutes (0=never)")

    # Notification settings
    notify_on_trigger = models.BooleanField(default=True)
    escalate_after_minutes = models.IntegerField(default=30, help_text="Escalate if not acknowledged (0=never)")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-severity", "vital_type", "name"]
        verbose_name = "Alert Rule"
        verbose_name_plural = "Alert Rules"

    def __str__(self):
        return f"{self.name} ({self.vital_type} {self.condition} {self.threshold_value})"

    def check_value(self, value: float) -> bool:
        """Check if a value triggers this alert rule."""
        threshold = float(self.threshold_value)
        threshold_high = float(self.threshold_value_high) if self.threshold_value_high else None

        if self.condition == "gt":
            return value > threshold
        elif self.condition == "gte":
            return value >= threshold
        elif self.condition == "lt":
            return value < threshold
        elif self.condition == "lte":
            return value <= threshold
        elif self.condition == "eq":
            return value == threshold
        elif self.condition == "range_outside" and threshold_high:
            return value < threshold or value > threshold_high
        return False


class Alert(models.Model):
    """Alert generated when vital signs exceed thresholds."""

    SEVERITY_CHOICES = [
        ("info", "Information"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("acknowledged", "Acknowledged"),
        ("resolved", "Resolved"),
        ("escalated", "Escalated"),
        ("auto_resolved", "Auto-Resolved"),
    ]

    # Alert identification
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="alerts")
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts")
    rule = models.ForeignKey(AlertRule, on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts")

    # Alert details
    vital_type = models.CharField(max_length=50)
    vital_value = models.DecimalField(max_digits=10, decimal_places=2)
    threshold_value = models.DecimalField(max_digits=10, decimal_places=2)
    condition = models.CharField(max_length=20)

    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="warning")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # Message
    title = models.CharField(max_length=255)
    message = models.TextField()

    # Timestamps
    triggered_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    escalated_at = models.DateTimeField(blank=True, null=True)

    # Actions
    acknowledged_by = models.CharField(max_length=200, blank=True)
    resolved_by = models.CharField(max_length=200, blank=True)
    resolution_notes = models.TextField(blank=True)

    # Related FHIR observation
    fhir_observation_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-triggered_at"]
        verbose_name = "Alert"
        verbose_name_plural = "Alerts"
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["status", "severity"]),
            models.Index(fields=["triggered_at"]),
        ]

    def __str__(self):
        return f"{self.severity.upper()}: {self.title} - {self.patient}"

    @property
    def is_active(self):
        return self.status == "active"

    @property
    def duration_seconds(self):
        """Time since alert was triggered."""
        from django.utils import timezone
        if self.resolved_at:
            return (self.resolved_at - self.triggered_at).total_seconds()
        return (timezone.now() - self.triggered_at).total_seconds()


class AlertNotification(models.Model):
    """Notification sent for an alert."""

    NOTIFICATION_TYPES = [
        ("dashboard", "Dashboard"),
        ("email", "Email"),
        ("sms", "SMS"),
        ("push", "Push Notification"),
        ("escalation", "Escalation"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
        ("read", "Read"),
    ]

    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    recipient = models.CharField(max_length=200, blank=True, help_text="Email, phone, or user ID")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    sent_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.notification_type} for {self.alert}"


# Default alert rules - populated on first migration
DEFAULT_ALERT_RULES = [
    # Critical rules
    {"name": "Critical Low SpO2", "vital_type": "oxygen_saturation", "condition": "lt",
     "threshold_value": 90, "severity": "critical", "description": "Oxygen saturation below 90% requires immediate attention"},
    {"name": "Critical High Heart Rate", "vital_type": "heart_rate", "condition": "gt",
     "threshold_value": 150, "severity": "critical", "description": "Heart rate above 150 bpm"},
    {"name": "Critical Low Heart Rate", "vital_type": "heart_rate", "condition": "lt",
     "threshold_value": 40, "severity": "critical", "description": "Heart rate below 40 bpm (severe bradycardia)"},
    {"name": "Critical High Systolic BP", "vital_type": "blood_pressure_systolic", "condition": "gt",
     "threshold_value": 180, "severity": "critical", "description": "Hypertensive crisis"},
    {"name": "Critical Low Systolic BP", "vital_type": "blood_pressure_systolic", "condition": "lt",
     "threshold_value": 80, "severity": "critical", "description": "Hypotensive shock risk"},
    {"name": "Critical High Temperature", "vital_type": "temperature", "condition": "gt",
     "threshold_value": 40.0, "severity": "critical", "description": "High fever requiring intervention"},

    # Warning rules
    {"name": "Low SpO2", "vital_type": "oxygen_saturation", "condition": "lt",
     "threshold_value": 94, "severity": "warning", "description": "Oxygen saturation below normal range"},
    {"name": "High Heart Rate", "vital_type": "heart_rate", "condition": "gt",
     "threshold_value": 100, "severity": "warning", "description": "Tachycardia"},
    {"name": "Low Heart Rate", "vital_type": "heart_rate", "condition": "lt",
     "threshold_value": 60, "severity": "warning", "description": "Bradycardia"},
    {"name": "High Systolic BP", "vital_type": "blood_pressure_systolic", "condition": "gt",
     "threshold_value": 140, "severity": "warning", "description": "Elevated blood pressure"},
    {"name": "Low Systolic BP", "vital_type": "blood_pressure_systolic", "condition": "lt",
     "threshold_value": 90, "severity": "warning", "description": "Low blood pressure"},
    {"name": "Fever", "vital_type": "temperature", "condition": "gt",
     "threshold_value": 38.0, "severity": "warning", "description": "Elevated temperature"},
    {"name": "High Respiratory Rate", "vital_type": "respiratory_rate", "condition": "gt",
     "threshold_value": 25, "severity": "warning", "description": "Tachypnea"},
    {"name": "Low Respiratory Rate", "vital_type": "respiratory_rate", "condition": "lt",
     "threshold_value": 10, "severity": "warning", "description": "Bradypnea"},

    # Info rules
    {"name": "Elevated Heart Rate", "vital_type": "heart_rate", "condition": "gt",
     "threshold_value": 90, "severity": "info", "description": "Heart rate slightly elevated"},
    {"name": "Slightly Low SpO2", "vital_type": "oxygen_saturation", "condition": "lt",
     "threshold_value": 96, "severity": "info", "description": "Oxygen saturation at lower end of normal"},
]
