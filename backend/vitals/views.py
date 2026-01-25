from __future__ import annotations

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated




from django.utils import timezone
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import VitalsEvent
from .tasks import run_orchestration


def _dt(obj, *names):
    """
    Return ISO timestamp for the first existing datetime-like field name.
    """
    for n in names:
        if hasattr(obj, n):
            v = getattr(obj, n)
            if v is None:
                continue
            return v.isoformat() if hasattr(v, "isoformat") else str(v)
    return None


def _val(obj, *names, default=None):
    """
    Return the first existing attribute among names.
    """
    for n in names:
        if hasattr(obj, n):
            return getattr(obj, n)
    return default


class VitalsEventView(APIView):
    """
    POST /api/v1/vitals/events
    Accepts a vitals event payload from a device/unifier.
    Stores it and triggers async orchestration (Celery -> LangGraph -> MCP tools -> FHIR).
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        payload = request.data or {}

        # Flexible field acceptance
        device_id = payload.get("device_id") or payload.get("deviceId") or payload.get("device")
        patient_id = payload.get("patient_id") or payload.get("patientId") or payload.get("patient")  # optional
        readings = payload.get("readings") or payload.get("measurements") or payload.get("data") or {}

        # Time field optional; store as now if absent
        effective_time = payload.get("effective_time") or payload.get("effectiveDateTime") or payload.get("timestamp")

        if not device_id:
            return Response({"error": "device_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(readings, dict):
            return Response({"error": "readings must be an object/dict"}, status=status.HTTP_400_BAD_REQUEST)

        # Create DB record with best-effort mapping to your model fields.
        # We don't know your exact model fields, so we set what we can safely.
        ev = VitalsEvent()

        # Common fields you likely have
        if hasattr(ev, "device_id"):
            ev.device_id = device_id
        if hasattr(ev, "patient_id") and patient_id is not None:
            ev.patient_id = patient_id

        # Payload/readings field name varies across versions
        if hasattr(ev, "readings"):
            ev.readings = readings
        elif hasattr(ev, "payload"):
            ev.payload = readings
        elif hasattr(ev, "data"):
            ev.data = readings

        # Effective time varies by field name; store if possible.
        # If your model doesn't have it, it will be skipped.
        if effective_time:
            # keep as string if your field is text; if it's DateTimeField, Django will parse ISO on save in many cases
            for fname in ("effective_time", "effectiveDateTime", "observed_at", "measured_at", "timestamp", "event_time"):
                if hasattr(ev, fname):
                    setattr(ev, fname, effective_time)
                    break

        # Fallback for created_at if present and empty
        if hasattr(ev, "created_at") and getattr(ev, "created_at", None) is None:
            try:
                ev.created_at = timezone.now()
            except Exception:
                pass

        ev.save()

        # Trigger async orchestration
        try:
            run_orchestration.delay(ev.id)
        except Exception as e:
            # Don't fail ingestion if queue is down; return accepted with warning.
            return Response(
                {
                    "id": ev.id,
                    "status": "stored",
                    "warning": f"orchestration not queued: {type(e).__name__}: {e}",
                },
                status=status.HTTP_202_ACCEPTED,
            )

        return Response({"id": ev.id, "status": "queued"}, status=status.HTTP_201_CREATED)

    def get(self, request):
        # Optional: simple list for quick debugging
        qs = VitalsEvent.objects.all().order_by("-id")[:50]
        items = []
        for ev in qs:
            items.append(
                {
                    "id": ev.id,
                    "patient_id": _val(ev, "patient_id", "patient", "patient_ref"),
                    "device_id": _val(ev, "device_id", "device", "device_ref"),
                    "effective_time": _dt(ev, "effective_time", "observed_at", "measured_at", "timestamp", "event_time", "created_at"),
                }
            )
        return Response(items, status=status.HTTP_200_OK)


class VitalsEventInternalView(APIView):
    """
    GET /api/v1/vitals/internal/events/<event_id>
    Internal/debug endpoint to inspect what was stored.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, event_id: int):
        ev = get_object_or_404(VitalsEvent, id=event_id)

        effective = _dt(
            ev,
            "effective_time",
            "effectiveDateTime",
            "observed_at",
            "measured_at",
            "timestamp",
            "event_time",
            "time",
            "created_at",
        )

        readings = _val(ev, "readings", "payload", "data", "measurements", default={})

        return Response(
            {
                "id": ev.id,
                "patient_id": _val(ev, "patient_id", "patient", "patient_ref"),
                "device_id": _val(ev, "device_id", "device", "device_ref"),
                "effective_time": effective,
                "readings": readings,
                "created_at": _dt(ev, "created_at"),
            },
            status=status.HTTP_200_OK,
        )

