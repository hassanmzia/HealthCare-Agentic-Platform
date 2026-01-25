from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Avg, Count, Q
from datetime import timedelta

from .models import Alert, AlertRule, AlertNotification, DEFAULT_ALERT_RULES
from .serializers import (
    AlertListSerializer, AlertDetailSerializer,
    AlertRuleSerializer,
    AcknowledgeAlertSerializer, ResolveAlertSerializer,
    AlertSummarySerializer, BulkAcknowledgeSerializer,
)


# Alert Views
class AlertListView(APIView):
    """List alerts with filtering."""

    def get(self, request):
        alerts = Alert.objects.select_related("patient", "device", "rule").all()

        # Filter by status
        alert_status = request.query_params.get("status")
        if alert_status:
            if alert_status == "active":
                alerts = alerts.filter(status="active")
            elif alert_status == "acknowledged":
                alerts = alerts.filter(status="acknowledged")
            elif alert_status == "resolved":
                alerts = alerts.filter(status__in=["resolved", "auto_resolved"])
            else:
                alerts = alerts.filter(status=alert_status)

        # Filter by severity
        severity = request.query_params.get("severity")
        if severity:
            alerts = alerts.filter(severity=severity)

        # Filter by patient
        patient_id = request.query_params.get("patient")
        if patient_id:
            alerts = alerts.filter(patient_id=patient_id)

        # Filter by vital type
        vital_type = request.query_params.get("vital_type")
        if vital_type:
            alerts = alerts.filter(vital_type=vital_type)

        # Date range
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        if start_date:
            alerts = alerts.filter(triggered_at__date__gte=start_date)
        if end_date:
            alerts = alerts.filter(triggered_at__date__lte=end_date)

        # Only active (for real-time dashboard)
        active_only = request.query_params.get("active_only")
        if active_only == "true":
            alerts = alerts.filter(status__in=["active", "escalated"])

        # Pagination
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))

        total = alerts.count()
        alerts = alerts[offset:offset + limit]

        serializer = AlertListSerializer(alerts, many=True)
        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": serializer.data
        })


class AlertDetailView(APIView):
    """Get details of a specific alert."""

    def get(self, request, alert_id):
        alert = get_object_or_404(Alert.objects.select_related("patient", "device", "rule"), id=alert_id)
        serializer = AlertDetailSerializer(alert)
        return Response(serializer.data)


class AcknowledgeAlertView(APIView):
    """Acknowledge an alert."""

    def post(self, request, alert_id):
        alert = get_object_or_404(Alert, id=alert_id)

        if alert.status not in ["active", "escalated"]:
            return Response(
                {"error": f"Cannot acknowledge alert with status '{alert.status}'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AcknowledgeAlertSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        alert.status = "acknowledged"
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = serializer.validated_data["acknowledged_by"]
        if serializer.validated_data.get("notes"):
            alert.resolution_notes = serializer.validated_data["notes"]
        alert.save()

        # Create notification record
        AlertNotification.objects.create(
            alert=alert,
            notification_type="dashboard",
            recipient=alert.acknowledged_by,
            status="read",
            sent_at=timezone.now(),
            read_at=timezone.now()
        )

        return Response(AlertDetailSerializer(alert).data)


class ResolveAlertView(APIView):
    """Resolve an alert."""

    def post(self, request, alert_id):
        alert = get_object_or_404(Alert, id=alert_id)

        if alert.status in ["resolved", "auto_resolved"]:
            return Response(
                {"error": "Alert is already resolved"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ResolveAlertSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        alert.status = "resolved"
        alert.resolved_at = timezone.now()
        alert.resolved_by = serializer.validated_data["resolved_by"]
        if serializer.validated_data.get("resolution_notes"):
            alert.resolution_notes = serializer.validated_data["resolution_notes"]
        alert.save()

        return Response(AlertDetailSerializer(alert).data)


class BulkAcknowledgeView(APIView):
    """Acknowledge multiple alerts at once."""

    def post(self, request):
        serializer = BulkAcknowledgeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        alert_ids = serializer.validated_data["alert_ids"]
        acknowledged_by = serializer.validated_data["acknowledged_by"]

        updated = Alert.objects.filter(
            id__in=alert_ids,
            status__in=["active", "escalated"]
        ).update(
            status="acknowledged",
            acknowledged_at=timezone.now(),
            acknowledged_by=acknowledged_by
        )

        return Response({"acknowledged_count": updated})


class AlertSummaryView(APIView):
    """Get summary statistics for alerts."""

    def get(self, request):
        today = timezone.now().date()

        # Active alerts by severity
        active_alerts = Alert.objects.filter(status__in=["active", "escalated"])

        # Calculate average response time for acknowledged alerts today
        acknowledged_today = Alert.objects.filter(
            acknowledged_at__date=today,
            status__in=["acknowledged", "resolved"]
        )

        avg_response = None
        if acknowledged_today.exists():
            # Calculate manually since we need difference between two datetime fields
            total_seconds = 0
            count = 0
            for alert in acknowledged_today:
                if alert.acknowledged_at:
                    total_seconds += (alert.acknowledged_at - alert.triggered_at).total_seconds()
                    count += 1
            if count > 0:
                avg_response = total_seconds / count

        summary = {
            "total_active": active_alerts.count(),
            "critical_count": active_alerts.filter(severity="critical").count(),
            "warning_count": active_alerts.filter(severity="warning").count(),
            "info_count": active_alerts.filter(severity="info").count(),
            "acknowledged_today": Alert.objects.filter(acknowledged_at__date=today).count(),
            "resolved_today": Alert.objects.filter(resolved_at__date=today).count(),
            "escalated_count": active_alerts.filter(status="escalated").count(),
            "average_response_time_seconds": avg_response,
        }

        return Response(summary)


# Alert Rule Views
class AlertRuleListView(APIView):
    """List and create alert rules."""

    def get(self, request):
        rules = AlertRule.objects.select_related("patient").all()

        # Filter by active status
        is_active = request.query_params.get("active")
        if is_active == "true":
            rules = rules.filter(is_active=True)
        elif is_active == "false":
            rules = rules.filter(is_active=False)

        # Filter by vital type
        vital_type = request.query_params.get("vital_type")
        if vital_type:
            rules = rules.filter(vital_type=vital_type)

        # Filter by severity
        severity = request.query_params.get("severity")
        if severity:
            rules = rules.filter(severity=severity)

        # Filter by patient (null for global)
        patient_id = request.query_params.get("patient")
        if patient_id == "global":
            rules = rules.filter(patient__isnull=True)
        elif patient_id:
            rules = rules.filter(Q(patient_id=patient_id) | Q(patient__isnull=True))

        serializer = AlertRuleSerializer(rules, many=True)
        return Response({"results": serializer.data})

    def post(self, request):
        serializer = AlertRuleSerializer(data=request.data)
        if serializer.is_valid():
            rule = serializer.save()
            return Response(AlertRuleSerializer(rule).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AlertRuleDetailView(APIView):
    """Get, update, or delete an alert rule."""

    def get(self, request, rule_id):
        rule = get_object_or_404(AlertRule, id=rule_id)
        serializer = AlertRuleSerializer(rule)
        return Response(serializer.data)

    def put(self, request, rule_id):
        rule = get_object_or_404(AlertRule, id=rule_id)
        serializer = AlertRuleSerializer(rule, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, rule_id):
        rule = get_object_or_404(AlertRule, id=rule_id)
        rule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InitializeDefaultRulesView(APIView):
    """Initialize default alert rules."""

    def post(self, request):
        created_count = 0
        for rule_data in DEFAULT_ALERT_RULES:
            # Check if rule with same name exists
            if not AlertRule.objects.filter(name=rule_data["name"]).exists():
                AlertRule.objects.create(**rule_data)
                created_count += 1

        return Response({
            "message": f"Created {created_count} default rules",
            "total_rules": AlertRule.objects.count()
        })


# Patient Alerts View
class PatientAlertsView(APIView):
    """Get alerts for a specific patient."""

    def get(self, request, patient_id):
        alerts = Alert.objects.filter(patient_id=patient_id).select_related("device", "rule")

        # Filter by status
        alert_status = request.query_params.get("status")
        if alert_status:
            alerts = alerts.filter(status=alert_status)

        # Active only
        active_only = request.query_params.get("active_only")
        if active_only == "true":
            alerts = alerts.filter(status__in=["active", "escalated"])

        limit = int(request.query_params.get("limit", 20))
        alerts = alerts[:limit]

        serializer = AlertListSerializer(alerts, many=True)
        return Response({"results": serializer.data})


# Check Vitals and Generate Alerts
class CheckVitalsView(APIView):
    """
    Check a vital sign value against rules and generate alerts if needed.
    Called by the IoT simulator or external systems.
    """

    def post(self, request):
        patient_id = request.data.get("patient_id")
        device_id = request.data.get("device_id")
        vital_type = request.data.get("vital_type")
        vital_value = request.data.get("vital_value")
        fhir_observation_id = request.data.get("fhir_observation_id", "")

        if not all([patient_id, vital_type, vital_value]):
            return Response(
                {"error": "patient_id, vital_type, and vital_value are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            vital_value = float(vital_value)
        except (TypeError, ValueError):
            return Response({"error": "vital_value must be a number"}, status=status.HTTP_400_BAD_REQUEST)

        # Get applicable rules (patient-specific or global)
        rules = AlertRule.objects.filter(
            vital_type=vital_type,
            is_active=True
        ).filter(
            Q(patient_id=patient_id) | Q(patient__isnull=True)
        ).order_by("-severity")  # Check critical rules first

        alerts_created = []

        for rule in rules:
            if rule.check_value(vital_value):
                # Check cooldown - don't create duplicate alerts
                cooldown_time = timezone.now() - timedelta(minutes=rule.cooldown_minutes)
                existing_alert = Alert.objects.filter(
                    patient_id=patient_id,
                    vital_type=vital_type,
                    rule=rule,
                    triggered_at__gte=cooldown_time,
                    status__in=["active", "acknowledged", "escalated"]
                ).first()

                if existing_alert:
                    continue  # Skip - still in cooldown

                # Create alert
                condition_display = dict(AlertRule.CONDITION_TYPES).get(rule.condition, rule.condition)
                vital_display = dict(AlertRule.VITAL_TYPES).get(vital_type, vital_type)

                alert = Alert.objects.create(
                    patient_id=patient_id,
                    device_id=device_id,
                    rule=rule,
                    vital_type=vital_type,
                    vital_value=vital_value,
                    threshold_value=rule.threshold_value,
                    condition=rule.condition,
                    severity=rule.severity,
                    title=f"{rule.severity.upper()}: {rule.name}",
                    message=f"{vital_display} is {vital_value}, which is {condition_display.lower()} {rule.threshold_value}. {rule.description}",
                    fhir_observation_id=fhir_observation_id
                )

                # Create dashboard notification
                AlertNotification.objects.create(
                    alert=alert,
                    notification_type="dashboard",
                    status="sent",
                    sent_at=timezone.now()
                )

                alerts_created.append(AlertListSerializer(alert).data)

        return Response({
            "checked": True,
            "vital_type": vital_type,
            "vital_value": vital_value,
            "alerts_created": len(alerts_created),
            "alerts": alerts_created
        })
