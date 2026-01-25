"""
Analytics API - Aggregation endpoints for dashboards and reporting.
"""

from datetime import datetime, timedelta
from collections import defaultdict

from django.db.models import Count, Avg, Max, Min, Q, F
from django.db.models.functions import TruncDate, TruncHour, ExtractHour
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from patients.models import Patient
from devices.models import Device, DeviceAssignment
from alerts.models import Alert, AlertRule
from clinical.models import Encounter, ClinicalNote, Diagnosis, CarePlan, Vitals


class OverviewStatsView(APIView):
    """Get high-level platform statistics."""

    def get(self, request):
        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Patient stats
        total_patients = Patient.objects.count()
        active_patients = Patient.objects.filter(is_active=True).count()
        new_patients_week = Patient.objects.filter(created_at__gte=week_ago).count()

        # Device stats
        total_devices = Device.objects.count()
        active_devices = Device.objects.filter(status="active").count()
        assigned_devices = Device.objects.filter(
            assignments__is_active=True
        ).distinct().count()

        # Alert stats
        active_alerts = Alert.objects.filter(status="active").count()
        critical_alerts = Alert.objects.filter(status="active", severity="critical").count()
        alerts_today = Alert.objects.filter(triggered_at__date=today).count()
        alerts_week = Alert.objects.filter(triggered_at__gte=week_ago).count()

        # Clinical stats
        active_encounters = Encounter.objects.filter(status="in_progress").count()
        encounters_today = Encounter.objects.filter(start_time__date=today).count()

        return Response({
            "patients": {
                "total": total_patients,
                "active": active_patients,
                "new_this_week": new_patients_week,
            },
            "devices": {
                "total": total_devices,
                "active": active_devices,
                "assigned": assigned_devices,
                "unassigned": active_devices - assigned_devices,
            },
            "alerts": {
                "active": active_alerts,
                "critical": critical_alerts,
                "today": alerts_today,
                "this_week": alerts_week,
            },
            "encounters": {
                "active": active_encounters,
                "today": encounters_today,
            },
            "generated_at": now.isoformat(),
        })


class VitalsAnalyticsView(APIView):
    """Get vitals statistics and trends."""

    def get(self, request):
        patient_id = request.query_params.get("patient_id")
        days = int(request.query_params.get("days", 7))

        now = timezone.now()
        start_date = now - timedelta(days=days)

        # Base queryset
        vitals_qs = Vitals.objects.filter(recorded_at__gte=start_date)
        if patient_id:
            vitals_qs = vitals_qs.filter(patient_id=patient_id)

        # Overall statistics
        stats = vitals_qs.aggregate(
            avg_heart_rate=Avg("heart_rate"),
            max_heart_rate=Max("heart_rate"),
            min_heart_rate=Min("heart_rate"),
            avg_systolic=Avg("blood_pressure_systolic"),
            max_systolic=Max("blood_pressure_systolic"),
            min_systolic=Min("blood_pressure_systolic"),
            avg_diastolic=Avg("blood_pressure_diastolic"),
            avg_spo2=Avg("oxygen_saturation"),
            min_spo2=Min("oxygen_saturation"),
            avg_temp=Avg("temperature"),
            max_temp=Max("temperature"),
            avg_resp_rate=Avg("respiratory_rate"),
            total_readings=Count("id"),
        )

        # Daily trends
        daily_trends = list(
            vitals_qs.annotate(date=TruncDate("recorded_at"))
            .values("date")
            .annotate(
                readings=Count("id"),
                avg_heart_rate=Avg("heart_rate"),
                avg_systolic=Avg("blood_pressure_systolic"),
                avg_diastolic=Avg("blood_pressure_diastolic"),
                avg_spo2=Avg("oxygen_saturation"),
                avg_temp=Avg("temperature"),
            )
            .order_by("date")
        )

        # Convert dates to strings for JSON serialization
        for trend in daily_trends:
            trend["date"] = trend["date"].isoformat() if trend["date"] else None

        # Abnormal readings count
        abnormal_counts = {
            "high_heart_rate": vitals_qs.filter(heart_rate__gt=100).count(),
            "low_heart_rate": vitals_qs.filter(heart_rate__lt=60).count(),
            "high_bp": vitals_qs.filter(blood_pressure_systolic__gt=140).count(),
            "low_spo2": vitals_qs.filter(oxygen_saturation__lt=95).count(),
            "fever": vitals_qs.filter(temperature__gt=38.0).count(),
        }

        return Response({
            "period_days": days,
            "statistics": stats,
            "daily_trends": daily_trends,
            "abnormal_counts": abnormal_counts,
            "generated_at": now.isoformat(),
        })


class AlertAnalyticsView(APIView):
    """Get alert statistics and trends."""

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        patient_id = request.query_params.get("patient_id")

        now = timezone.now()
        start_date = now - timedelta(days=days)

        # Base queryset
        alerts_qs = Alert.objects.filter(triggered_at__gte=start_date)
        if patient_id:
            alerts_qs = alerts_qs.filter(patient_id=patient_id)

        # Count by severity
        by_severity = dict(
            alerts_qs.values("severity")
            .annotate(count=Count("id"))
            .values_list("severity", "count")
        )

        # Count by status
        by_status = dict(
            alerts_qs.values("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )

        # Count by vital type
        by_vital_type = dict(
            alerts_qs.values("vital_type")
            .annotate(count=Count("id"))
            .values_list("vital_type", "count")
        )

        # Daily trends
        daily_trends = list(
            alerts_qs.annotate(date=TruncDate("triggered_at"))
            .values("date")
            .annotate(
                total=Count("id"),
                critical=Count("id", filter=Q(severity="critical")),
                warning=Count("id", filter=Q(severity="warning")),
                info=Count("id", filter=Q(severity="info")),
            )
            .order_by("date")
        )

        for trend in daily_trends:
            trend["date"] = trend["date"].isoformat() if trend["date"] else None

        # Hourly distribution (what hours see most alerts)
        hourly_dist = list(
            alerts_qs.annotate(hour=ExtractHour("triggered_at"))
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("hour")
        )

        # Response time stats (time to acknowledge)
        acknowledged_alerts = alerts_qs.filter(
            acknowledged_at__isnull=False
        ).annotate(
            response_seconds=F("acknowledged_at") - F("triggered_at")
        )

        # Calculate average response time manually
        response_times = []
        for alert in acknowledged_alerts[:1000]:  # Limit for performance
            if alert.acknowledged_at and alert.triggered_at:
                delta = alert.acknowledged_at - alert.triggered_at
                response_times.append(delta.total_seconds())

        avg_response_time = sum(response_times) / len(response_times) if response_times else None

        # Top triggered rules
        top_rules = list(
            alerts_qs.filter(rule__isnull=False)
            .values("rule__name", "rule__severity")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # Top patients with alerts
        top_patients = list(
            alerts_qs.values("patient__first_name", "patient__last_name", "patient_id")
            .annotate(
                alert_count=Count("id"),
                critical_count=Count("id", filter=Q(severity="critical")),
            )
            .order_by("-alert_count")[:10]
        )

        return Response({
            "period_days": days,
            "total_alerts": alerts_qs.count(),
            "by_severity": by_severity,
            "by_status": by_status,
            "by_vital_type": by_vital_type,
            "daily_trends": daily_trends,
            "hourly_distribution": hourly_dist,
            "response_metrics": {
                "avg_response_time_seconds": avg_response_time,
                "total_acknowledged": len(response_times),
            },
            "top_rules": top_rules,
            "top_patients": top_patients,
            "generated_at": now.isoformat(),
        })


class DeviceAnalyticsView(APIView):
    """Get device utilization and status metrics."""

    def get(self, request):
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Device status distribution
        status_dist = dict(
            Device.objects.values("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )

        # Device type distribution
        type_dist = dict(
            Device.objects.values("device_type")
            .annotate(count=Count("id"))
            .values_list("device_type", "count")
        )

        # Assignment stats
        total_devices = Device.objects.count()
        assigned_count = Device.objects.filter(
            assignments__is_active=True
        ).distinct().count()

        # Assignments over time
        assignment_trends = list(
            DeviceAssignment.objects.filter(assigned_at__gte=month_ago)
            .annotate(date=TruncDate("assigned_at"))
            .values("date")
            .annotate(
                new_assignments=Count("id"),
            )
            .order_by("date")
        )

        for trend in assignment_trends:
            trend["date"] = trend["date"].isoformat() if trend["date"] else None

        # Devices by capability
        capability_counts = defaultdict(int)
        for device in Device.objects.all():
            for cap in (device.capabilities or []):
                capability_counts[cap] += 1

        # Most used devices (by number of assignments)
        most_used = list(
            Device.objects.annotate(
                assignment_count=Count("assignments")
            )
            .filter(assignment_count__gt=0)
            .values("device_id", "name", "device_type", "assignment_count")
            .order_by("-assignment_count")[:10]
        )

        # Devices needing attention (inactive but assigned)
        needs_attention = Device.objects.filter(
            ~Q(status="active"),
            assignments__is_active=True
        ).distinct().count()

        return Response({
            "total_devices": total_devices,
            "status_distribution": status_dist,
            "type_distribution": type_dist,
            "assignment_stats": {
                "assigned": assigned_count,
                "unassigned": total_devices - assigned_count,
                "utilization_rate": round(assigned_count / total_devices * 100, 1) if total_devices > 0 else 0,
            },
            "assignment_trends": assignment_trends,
            "capability_distribution": dict(capability_counts),
            "most_used_devices": most_used,
            "needs_attention": needs_attention,
            "generated_at": now.isoformat(),
        })


class PatientAnalyticsView(APIView):
    """Get patient population analytics."""

    def get(self, request):
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Basic stats
        total_patients = Patient.objects.count()
        active_patients = Patient.objects.filter(is_active=True).count()

        # Gender distribution
        gender_dist = dict(
            Patient.objects.values("gender")
            .annotate(count=Count("id"))
            .values_list("gender", "count")
        )

        # Age distribution (calculated from date_of_birth)
        age_groups = {
            "0-17": 0,
            "18-30": 0,
            "31-50": 0,
            "51-70": 0,
            "71+": 0,
            "unknown": 0,
        }

        today = now.date()
        for patient in Patient.objects.all():
            if patient.date_of_birth:
                age = (today - patient.date_of_birth).days // 365
                if age < 18:
                    age_groups["0-17"] += 1
                elif age <= 30:
                    age_groups["18-30"] += 1
                elif age <= 50:
                    age_groups["31-50"] += 1
                elif age <= 70:
                    age_groups["51-70"] += 1
                else:
                    age_groups["71+"] += 1
            else:
                age_groups["unknown"] += 1

        # New patients trend
        new_patient_trends = list(
            Patient.objects.filter(created_at__gte=month_ago)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        for trend in new_patient_trends:
            trend["date"] = trend["date"].isoformat() if trend["date"] else None

        # Patients with active alerts
        patients_with_alerts = Alert.objects.filter(
            status="active"
        ).values("patient_id").distinct().count()

        # Patients with active encounters
        patients_in_encounters = Encounter.objects.filter(
            status="in_progress"
        ).values("patient_id").distinct().count()

        # Patients with assigned devices
        patients_with_devices = DeviceAssignment.objects.filter(
            is_active=True
        ).values("patient_id").distinct().count()

        # Top diagnoses
        top_diagnoses = list(
            Diagnosis.objects.filter(status="active")
            .values("icd10_code", "description")
            .annotate(patient_count=Count("patient_id", distinct=True))
            .order_by("-patient_count")[:10]
        )

        return Response({
            "total_patients": total_patients,
            "active_patients": active_patients,
            "gender_distribution": gender_dist,
            "age_distribution": age_groups,
            "new_patient_trends": new_patient_trends,
            "engagement": {
                "with_active_alerts": patients_with_alerts,
                "in_encounters": patients_in_encounters,
                "with_devices": patients_with_devices,
            },
            "top_diagnoses": top_diagnoses,
            "generated_at": now.isoformat(),
        })


class ClinicalAnalyticsView(APIView):
    """Get clinical workflow analytics."""

    def get(self, request):
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Encounter stats
        encounter_by_type = dict(
            Encounter.objects.values("encounter_type")
            .annotate(count=Count("id"))
            .values_list("encounter_type", "count")
        )

        encounter_by_status = dict(
            Encounter.objects.values("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )

        # Encounter trends
        encounter_trends = list(
            Encounter.objects.filter(start_time__gte=month_ago)
            .annotate(date=TruncDate("start_time"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        for trend in encounter_trends:
            trend["date"] = trend["date"].isoformat() if trend["date"] else None

        # Note stats
        notes_by_type = dict(
            ClinicalNote.objects.values("note_type")
            .annotate(count=Count("id"))
            .values_list("note_type", "count")
        )

        notes_by_status = dict(
            ClinicalNote.objects.values("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )

        # Care plan stats
        careplan_by_status = dict(
            CarePlan.objects.values("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )

        careplan_by_category = dict(
            CarePlan.objects.values("category")
            .annotate(count=Count("id"))
            .values_list("category", "count")
        )

        # Top authors
        top_note_authors = list(
            ClinicalNote.objects.filter(note_datetime__gte=month_ago)
            .values("author")
            .annotate(note_count=Count("id"))
            .order_by("-note_count")[:10]
        )

        # Diagnosis stats
        diagnosis_by_status = dict(
            Diagnosis.objects.values("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )

        diagnosis_by_category = dict(
            Diagnosis.objects.values("category")
            .annotate(count=Count("id"))
            .values_list("category", "count")
        )

        return Response({
            "encounters": {
                "by_type": encounter_by_type,
                "by_status": encounter_by_status,
                "trends": encounter_trends,
                "total": Encounter.objects.count(),
                "active": Encounter.objects.filter(status="in_progress").count(),
            },
            "notes": {
                "by_type": notes_by_type,
                "by_status": notes_by_status,
                "total": ClinicalNote.objects.count(),
                "this_week": ClinicalNote.objects.filter(note_datetime__gte=week_ago).count(),
                "top_authors": top_note_authors,
            },
            "care_plans": {
                "by_status": careplan_by_status,
                "by_category": careplan_by_category,
                "total": CarePlan.objects.count(),
                "active": CarePlan.objects.filter(status="active").count(),
            },
            "diagnoses": {
                "by_status": diagnosis_by_status,
                "by_category": diagnosis_by_category,
                "total": Diagnosis.objects.count(),
                "active": Diagnosis.objects.filter(status="active").count(),
            },
            "generated_at": now.isoformat(),
        })
