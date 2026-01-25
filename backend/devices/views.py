import httpx
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Device, DeviceAssignment
from .serializers import (
    DeviceListSerializer,
    DeviceDetailSerializer,
    DeviceAssignmentSerializer,
    AssignDeviceSerializer,
    UnassignDeviceSerializer,
)
from patients.models import Patient

FHIR_BASE = "http://hapi-fhir:8080/fhir"


async def sync_device_to_fhir(device: Device) -> str:
    """Create or update device in FHIR server and return FHIR ID."""
    fhir_device = {
        "resourceType": "Device",
        "identifier": [
            {"system": "urn:device:id", "value": device.device_id}
        ],
        "status": "active" if device.status == "active" else "inactive",
        "deviceName": [
            {"name": device.name, "type": "user-friendly-name"}
        ],
    }

    if device.serial_number:
        fhir_device["identifier"].append({
            "system": "urn:device:serial",
            "value": device.serial_number
        })

    if device.manufacturer:
        fhir_device["manufacturer"] = device.manufacturer

    if device.model_number:
        fhir_device["modelNumber"] = device.model_number

    # Add device type
    device_type_codes = {
        "vital_monitor": {"code": "vital-monitor", "display": "Vital Signs Monitor"},
        "pulse_oximeter": {"code": "pulse-oximeter", "display": "Pulse Oximeter"},
        "bp_monitor": {"code": "bp-monitor", "display": "Blood Pressure Monitor"},
        "thermometer": {"code": "thermometer", "display": "Thermometer"},
        "ecg_monitor": {"code": "ecg-monitor", "display": "ECG Monitor"},
        "glucose_monitor": {"code": "glucose-monitor", "display": "Glucose Monitor"},
        "weight_scale": {"code": "weight-scale", "display": "Weight Scale"},
        "multi_parameter": {"code": "multi-param", "display": "Multi-Parameter Monitor"},
        "wearable": {"code": "wearable", "display": "Wearable Device"},
    }
    if device.device_type in device_type_codes:
        fhir_device["type"] = {
            "coding": [{
                "system": "urn:device:type",
                **device_type_codes[device.device_type]
            }]
        }

    headers = {"Content-Type": "application/fhir+json"}

    async with httpx.AsyncClient(timeout=30) as client:
        if device.fhir_id:
            fhir_device["id"] = device.fhir_id
            r = await client.put(
                f"{FHIR_BASE}/Device/{device.fhir_id}",
                json=fhir_device,
                headers=headers
            )
        else:
            r = await client.post(
                f"{FHIR_BASE}/Device",
                json=fhir_device,
                headers=headers
            )

        if r.status_code in (200, 201):
            return r.json().get("id")
        else:
            print(f"FHIR device sync error: {r.status_code} - {r.text}")
            return None


def sync_device_to_fhir_sync(device: Device) -> str:
    """Synchronous version of FHIR sync."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(sync_device_to_fhir(device))


class DeviceListView(APIView):
    """List all devices or create a new device."""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        queryset = Device.objects.all()

        # Search
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(device_id__icontains=search) |
                models.Q(serial_number__icontains=search)
            )

        # Filter by status
        device_status = request.query_params.get("status")
        if device_status:
            queryset = queryset.filter(status=device_status)

        # Filter by type
        device_type = request.query_params.get("type")
        if device_type:
            queryset = queryset.filter(device_type=device_type)

        # Filter by assignment status
        assigned = request.query_params.get("assigned")
        if assigned == "true":
            queryset = queryset.filter(assignments__is_active=True).distinct()
        elif assigned == "false":
            queryset = queryset.exclude(assignments__is_active=True)

        # Filter by facility
        facility = request.query_params.get("facility")
        if facility:
            queryset = queryset.filter(facility__icontains=facility)

        # Pagination
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))
        total = queryset.count()
        queryset = queryset[offset:offset + limit]

        serializer = DeviceListSerializer(queryset, many=True)
        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": serializer.data
        })

    def post(self, request):
        serializer = DeviceDetailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        device = serializer.save()

        # Sync to FHIR
        try:
            fhir_id = sync_device_to_fhir_sync(device)
            if fhir_id:
                device.fhir_id = fhir_id
                device.save(update_fields=["fhir_id"])
        except Exception as e:
            print(f"FHIR sync failed: {e}")

        return Response(
            DeviceDetailSerializer(device).data,
            status=status.HTTP_201_CREATED
        )


class DeviceDetailView(APIView):
    """Retrieve, update or delete a device."""
    authentication_classes = []
    permission_classes = []

    def get(self, request, device_id):
        device = get_object_or_404(Device, id=device_id)
        serializer = DeviceDetailSerializer(device)
        return Response(serializer.data)

    def put(self, request, device_id):
        device = get_object_or_404(Device, id=device_id)
        serializer = DeviceDetailSerializer(device, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        device = serializer.save()

        # Sync to FHIR
        try:
            fhir_id = sync_device_to_fhir_sync(device)
            if fhir_id and not device.fhir_id:
                device.fhir_id = fhir_id
                device.save(update_fields=["fhir_id"])
        except Exception as e:
            print(f"FHIR sync failed: {e}")

        return Response(DeviceDetailSerializer(device).data)

    def delete(self, request, device_id):
        device = get_object_or_404(Device, id=device_id)
        # Soft delete - set to retired
        device.status = "retired"
        device.save(update_fields=["status"])
        # Deactivate any active assignments
        DeviceAssignment.objects.filter(device=device, is_active=True).update(
            is_active=False,
            unassigned_at=timezone.now()
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeviceAssignView(APIView):
    """Assign a device to a patient."""
    authentication_classes = []
    permission_classes = []

    def post(self, request, device_id):
        device = get_object_or_404(Device, id=device_id)
        serializer = AssignDeviceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        patient = get_object_or_404(Patient, id=serializer.validated_data["patient_id"])

        # Create new assignment (will auto-deactivate previous)
        assignment = DeviceAssignment.objects.create(
            device=device,
            patient=patient,
            assigned_by=serializer.validated_data.get("assigned_by", ""),
            reason=serializer.validated_data.get("reason", ""),
            notes=serializer.validated_data.get("notes", ""),
            is_active=True
        )

        return Response(
            DeviceAssignmentSerializer(assignment).data,
            status=status.HTTP_201_CREATED
        )


class DeviceUnassignView(APIView):
    """Unassign a device from its current patient."""
    authentication_classes = []
    permission_classes = []

    def post(self, request, device_id):
        device = get_object_or_404(Device, id=device_id)
        serializer = UnassignDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assignment = device.current_assignment
        if not assignment:
            return Response(
                {"error": "Device is not currently assigned"},
                status=status.HTTP_400_BAD_REQUEST
            )

        assignment.is_active = False
        assignment.unassigned_at = timezone.now()
        if serializer.validated_data.get("notes"):
            assignment.notes += f"\nUnassignment note: {serializer.validated_data['notes']}"
        assignment.save()

        return Response(
            DeviceAssignmentSerializer(assignment).data,
            status=status.HTTP_200_OK
        )


class DeviceByDeviceIdView(APIView):
    """Get device by device_id (not primary key)."""
    authentication_classes = []
    permission_classes = []

    def get(self, request, device_id):
        device = get_object_or_404(Device, device_id=device_id)
        serializer = DeviceDetailSerializer(device)
        return Response(serializer.data)


class PatientDevicesView(APIView):
    """Get all devices assigned to a patient."""
    authentication_classes = []
    permission_classes = []

    def get(self, request, patient_id):
        patient = get_object_or_404(Patient, id=patient_id)
        active_only = request.query_params.get("active", "true").lower() == "true"

        assignments = patient.device_assignments.all()
        if active_only:
            assignments = assignments.filter(is_active=True)

        serializer = DeviceAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)


class DeviceAssignmentHistoryView(APIView):
    """Get assignment history for a device."""
    authentication_classes = []
    permission_classes = []

    def get(self, request, device_id):
        device = get_object_or_404(Device, id=device_id)
        assignments = device.assignments.all()
        serializer = DeviceAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)
