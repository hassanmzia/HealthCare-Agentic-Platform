from rest_framework import serializers
from .models import Device, DeviceAssignment
from patients.serializers import PatientListSerializer


class DeviceAssignmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    patient_mrn = serializers.SerializerMethodField()

    class Meta:
        model = DeviceAssignment
        fields = [
            "id", "device", "patient", "patient_name", "patient_mrn",
            "assigned_at", "unassigned_at", "is_active",
            "assigned_by", "reason", "notes"
        ]
        read_only_fields = ["id", "assigned_at", "unassigned_at"]

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None

    def get_patient_mrn(self, obj):
        return obj.patient.mrn if obj.patient else None


class DeviceAssignmentListSerializer(serializers.ModelSerializer):
    """Serializer for assignment info in device list."""
    patient_name = serializers.SerializerMethodField()
    patient_fhir_id = serializers.SerializerMethodField()

    class Meta:
        model = DeviceAssignment
        fields = ["id", "patient", "patient_name", "patient_fhir_id", "assigned_at", "is_active"]

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient else None

    def get_patient_fhir_id(self, obj):
        return obj.patient.fhir_id if obj.patient else None


class DeviceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    assigned_patient_name = serializers.SerializerMethodField()
    assigned_patient_id = serializers.SerializerMethodField()
    current_assignment = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = [
            "id", "device_id", "fhir_id", "name", "device_type",
            "manufacturer", "status", "facility", "department",
            "room", "bed", "last_seen", "battery_level", "capabilities",
            "assigned_patient_name", "assigned_patient_id", "current_assignment", "created_at"
        ]

    def get_assigned_patient_name(self, obj):
        patient = obj.assigned_patient
        return patient.full_name if patient else None

    def get_assigned_patient_id(self, obj):
        patient = obj.assigned_patient
        return patient.id if patient else None

    def get_current_assignment(self, obj):
        assignment = obj.current_assignment
        if assignment:
            return DeviceAssignmentListSerializer(assignment).data
        return None


class DeviceDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail/create/update views."""
    assigned_patient = PatientListSerializer(read_only=True)
    current_assignment = DeviceAssignmentSerializer(read_only=True)
    assignments = DeviceAssignmentSerializer(many=True, read_only=True)

    class Meta:
        model = Device
        fields = [
            "id", "device_id", "fhir_id", "serial_number",
            "name", "device_type", "manufacturer", "model_number", "firmware_version",
            "facility", "department", "room", "bed",
            "capabilities", "reading_interval_seconds", "config",
            "status", "last_seen", "battery_level",
            "notes", "created_at", "updated_at",
            "assigned_patient", "current_assignment", "assignments"
        ]
        read_only_fields = ["id", "fhir_id", "created_at", "updated_at", "last_seen"]


class AssignDeviceSerializer(serializers.Serializer):
    """Serializer for assigning a device to a patient."""
    patient_id = serializers.IntegerField()
    assigned_by = serializers.CharField(required=False, allow_blank=True)
    reason = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class UnassignDeviceSerializer(serializers.Serializer):
    """Serializer for unassigning a device from a patient."""
    notes = serializers.CharField(required=False, allow_blank=True)
