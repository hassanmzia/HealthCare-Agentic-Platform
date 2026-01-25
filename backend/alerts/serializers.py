from rest_framework import serializers
from .models import Alert, AlertRule, AlertNotification


class AlertRuleSerializer(serializers.ModelSerializer):
    """Serializer for alert rules."""
    patient_name = serializers.CharField(source="patient.full_name", read_only=True, allow_null=True)
    vital_type_display = serializers.CharField(source="get_vital_type_display", read_only=True)
    condition_display = serializers.CharField(source="get_condition_display", read_only=True)
    severity_display = serializers.CharField(source="get_severity_display", read_only=True)

    class Meta:
        model = AlertRule
        fields = [
            "id", "name", "description",
            "vital_type", "vital_type_display",
            "condition", "condition_display",
            "threshold_value", "threshold_value_high",
            "severity", "severity_display",
            "patient", "patient_name",
            "is_active", "cooldown_minutes", "auto_acknowledge_minutes",
            "notify_on_trigger", "escalate_after_minutes",
            "created_at", "updated_at", "created_by"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AlertNotificationSerializer(serializers.ModelSerializer):
    """Serializer for alert notifications."""

    class Meta:
        model = AlertNotification
        fields = [
            "id", "alert", "notification_type", "recipient",
            "status", "sent_at", "read_at", "error_message"
        ]
        read_only_fields = ["id", "sent_at"]


class AlertListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for alert lists."""
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    patient_mrn = serializers.CharField(source="patient.mrn", read_only=True)
    device_name = serializers.CharField(source="device.name", read_only=True, allow_null=True)
    severity_display = serializers.CharField(source="get_severity_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)

    class Meta:
        model = Alert
        fields = [
            "id", "patient", "patient_name", "patient_mrn",
            "device", "device_name",
            "vital_type", "vital_value", "threshold_value",
            "severity", "severity_display",
            "status", "status_display",
            "title", "triggered_at",
            "acknowledged_at", "acknowledged_by",
            "duration_seconds"
        ]


class AlertDetailSerializer(serializers.ModelSerializer):
    """Full serializer for alert details."""
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    patient_mrn = serializers.CharField(source="patient.mrn", read_only=True)
    device_name = serializers.CharField(source="device.name", read_only=True, allow_null=True)
    rule_name = serializers.CharField(source="rule.name", read_only=True, allow_null=True)
    severity_display = serializers.CharField(source="get_severity_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    notifications = AlertNotificationSerializer(many=True, read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)

    class Meta:
        model = Alert
        fields = [
            "id", "patient", "patient_name", "patient_mrn",
            "device", "device_name",
            "rule", "rule_name",
            "vital_type", "vital_value", "threshold_value", "condition",
            "severity", "severity_display",
            "status", "status_display",
            "title", "message",
            "triggered_at", "acknowledged_at", "resolved_at", "escalated_at",
            "acknowledged_by", "resolved_by", "resolution_notes",
            "fhir_observation_id",
            "notifications", "duration_seconds"
        ]
        read_only_fields = ["id", "triggered_at", "duration_seconds"]


class AcknowledgeAlertSerializer(serializers.Serializer):
    """Serializer for acknowledging an alert."""
    acknowledged_by = serializers.CharField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class ResolveAlertSerializer(serializers.Serializer):
    """Serializer for resolving an alert."""
    resolved_by = serializers.CharField(required=True)
    resolution_notes = serializers.CharField(required=False, allow_blank=True)


class AlertSummarySerializer(serializers.Serializer):
    """Summary statistics for alerts."""
    total_active = serializers.IntegerField()
    critical_count = serializers.IntegerField()
    warning_count = serializers.IntegerField()
    info_count = serializers.IntegerField()
    acknowledged_today = serializers.IntegerField()
    resolved_today = serializers.IntegerField()
    escalated_count = serializers.IntegerField()
    average_response_time_seconds = serializers.FloatField(allow_null=True)


class BulkAcknowledgeSerializer(serializers.Serializer):
    """Serializer for bulk acknowledging alerts."""
    alert_ids = serializers.ListField(child=serializers.IntegerField())
    acknowledged_by = serializers.CharField(required=True)
