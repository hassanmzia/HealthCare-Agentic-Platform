from rest_framework import serializers
from .models import Encounter, ClinicalNote, Diagnosis, CarePlan, Vitals


class EncounterListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for encounter lists."""
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    patient_mrn = serializers.CharField(source="patient.mrn", read_only=True)

    class Meta:
        model = Encounter
        fields = [
            "id", "patient", "patient_name", "patient_mrn", "fhir_id",
            "encounter_type", "status", "priority",
            "start_time", "end_time", "facility", "department",
            "attending_physician", "chief_complaint", "created_at"
        ]


class EncounterDetailSerializer(serializers.ModelSerializer):
    """Full serializer for encounter details."""
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    patient_mrn = serializers.CharField(source="patient.mrn", read_only=True)

    class Meta:
        model = Encounter
        fields = [
            "id", "patient", "patient_name", "patient_mrn", "fhir_id",
            "encounter_type", "status", "priority",
            "start_time", "end_time",
            "facility", "department", "room", "bed",
            "attending_physician", "attending_physician_id",
            "chief_complaint", "reason_codes", "notes",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ClinicalNoteListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for note lists."""
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    encounter_type = serializers.CharField(source="encounter.encounter_type", read_only=True, allow_null=True)

    class Meta:
        model = ClinicalNote
        fields = [
            "id", "patient", "patient_name", "encounter", "encounter_type",
            "note_type", "status", "title", "author", "author_role",
            "note_datetime", "signed_datetime", "created_at"
        ]


class ClinicalNoteDetailSerializer(serializers.ModelSerializer):
    """Full serializer for clinical note details."""
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    patient_mrn = serializers.CharField(source="patient.mrn", read_only=True)

    class Meta:
        model = ClinicalNote
        fields = [
            "id", "patient", "patient_name", "patient_mrn", "encounter",
            "note_type", "status", "title",
            "subjective", "objective", "assessment", "plan", "content",
            "author", "author_role", "co_signer",
            "note_datetime", "signed_datetime",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DiagnosisSerializer(serializers.ModelSerializer):
    """Serializer for diagnoses."""
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = Diagnosis
        fields = [
            "id", "patient", "patient_name", "encounter",
            "icd10_code", "description", "category", "status",
            "onset_date", "resolution_date", "severity", "clinical_notes",
            "diagnosed_by", "diagnosed_date",
            "is_primary", "rank",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "diagnosed_date", "created_at", "updated_at"]


class CarePlanListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for care plan lists."""
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = CarePlan
        fields = [
            "id", "patient", "patient_name", "encounter",
            "title", "category", "status",
            "start_date", "end_date", "created_by", "created_at"
        ]


class CarePlanDetailSerializer(serializers.ModelSerializer):
    """Full serializer for care plan details."""
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    diagnoses = DiagnosisSerializer(source="addresses_diagnoses", many=True, read_only=True)

    class Meta:
        model = CarePlan
        fields = [
            "id", "patient", "patient_name", "encounter",
            "title", "category", "status", "description",
            "goals", "activities",
            "start_date", "end_date",
            "addresses_diagnoses", "diagnoses",
            "created_by", "care_team",
            "patient_instructions", "follow_up_instructions",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class VitalsSerializer(serializers.ModelSerializer):
    """Serializer for vitals records."""
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    blood_pressure = serializers.CharField(read_only=True)

    class Meta:
        model = Vitals
        fields = [
            "id", "patient", "patient_name", "encounter",
            "heart_rate", "blood_pressure_systolic", "blood_pressure_diastolic", "blood_pressure",
            "respiratory_rate", "temperature", "oxygen_saturation",
            "weight", "height", "bmi", "pain_level",
            "recorded_at", "recorded_by", "method", "device_id", "notes",
            "created_at"
        ]
        read_only_fields = ["id", "created_at", "blood_pressure"]


class PatientClinicalSummarySerializer(serializers.Serializer):
    """Summary of patient clinical information for doctor portal."""
    patient_id = serializers.IntegerField()
    patient_name = serializers.CharField()
    patient_mrn = serializers.CharField()
    age = serializers.IntegerField()
    gender = serializers.CharField()

    active_encounters = EncounterListSerializer(many=True)
    recent_notes = ClinicalNoteListSerializer(many=True)
    active_diagnoses = DiagnosisSerializer(many=True)
    active_care_plans = CarePlanListSerializer(many=True)
    latest_vitals = VitalsSerializer(allow_null=True)

    allergies = serializers.ListField(child=serializers.CharField())
    medications = serializers.ListField(child=serializers.CharField())
