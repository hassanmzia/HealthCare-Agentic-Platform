from rest_framework import serializers
from .models import (
    MedicationCatalog,
    DrugInteraction,
    PatientAllergy,
    Prescription,
    MedicationAdministration,
)


class MedicationCatalogSerializer(serializers.ModelSerializer):
    """Serializer for medication catalog entries."""

    class Meta:
        model = MedicationCatalog
        fields = [
            "id",
            "rxnorm_code",
            "ndc_code",
            "generic_name",
            "brand_names",
            "category",
            "drug_class",
            "form",
            "route",
            "strength",
            "unit",
            "typical_dose_min",
            "typical_dose_max",
            "max_daily_dose",
            "frequency_options",
            "contraindications",
            "warnings",
            "side_effects",
            "is_controlled",
            "controlled_schedule",
            "requires_monitoring",
            "monitoring_parameters",
            "is_high_alert",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MedicationCatalogListSerializer(serializers.ModelSerializer):
    """Compact serializer for medication lists."""

    class Meta:
        model = MedicationCatalog
        fields = [
            "id",
            "rxnorm_code",
            "generic_name",
            "brand_names",
            "category",
            "form",
            "route",
            "strength",
            "is_controlled",
            "is_high_alert",
            "is_active",
        ]


class DrugInteractionSerializer(serializers.ModelSerializer):
    """Serializer for drug interactions."""

    drug_a_name = serializers.CharField(source="drug_a.generic_name", read_only=True)
    drug_b_name = serializers.CharField(source="drug_b.generic_name", read_only=True)

    class Meta:
        model = DrugInteraction
        fields = [
            "id",
            "drug_a",
            "drug_a_name",
            "drug_b",
            "drug_b_name",
            "severity",
            "description",
            "clinical_effects",
            "management",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PatientAllergySerializer(serializers.ModelSerializer):
    """Serializer for patient allergies."""

    patient_name = serializers.SerializerMethodField()
    medication_name = serializers.CharField(source="medication.generic_name", read_only=True)

    class Meta:
        model = PatientAllergy
        fields = [
            "id",
            "patient",
            "patient_name",
            "allergen_type",
            "allergen_name",
            "medication",
            "medication_name",
            "reaction_type",
            "severity",
            "reaction_description",
            "onset_date",
            "is_active",
            "verified",
            "verified_by",
            "verified_at",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"


class PrescriptionSerializer(serializers.ModelSerializer):
    """Full serializer for prescriptions."""

    patient_name = serializers.SerializerMethodField()
    medication_name = serializers.CharField(source="medication.generic_name", read_only=True)
    medication_details = MedicationCatalogListSerializer(source="medication", read_only=True)
    administrations_count = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = [
            "id",
            "prescription_number",
            "fhir_id",
            "patient",
            "patient_name",
            "medication",
            "medication_name",
            "medication_details",
            "dose_quantity",
            "dose_unit",
            "route",
            "frequency",
            "frequency_hours",
            "start_date",
            "end_date",
            "duration_days",
            "quantity_prescribed",
            "refills_allowed",
            "refills_remaining",
            "prn_reason",
            "max_prn_doses_per_day",
            "indication",
            "diagnosis_codes",
            "special_instructions",
            "prescriber_name",
            "prescriber_id",
            "prescriber_npi",
            "status",
            "priority",
            "pharmacy_notes",
            "dispensed_at",
            "dispensed_by",
            "allergy_check_passed",
            "interaction_check_passed",
            "interaction_warnings",
            "hold_reason",
            "held_at",
            "held_by",
            "discontinued_reason",
            "discontinued_at",
            "discontinued_by",
            "prescribed_at",
            "updated_at",
            "administrations_count",
        ]
        read_only_fields = [
            "id",
            "prescription_number",
            "prescribed_at",
            "updated_at",
            "allergy_check_passed",
            "interaction_check_passed",
            "interaction_warnings",
        ]

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    def get_administrations_count(self, obj):
        return obj.administrations.count()


class PrescriptionListSerializer(serializers.ModelSerializer):
    """Compact serializer for prescription lists."""

    patient_name = serializers.SerializerMethodField()
    medication_name = serializers.CharField(source="medication.generic_name", read_only=True)
    is_high_alert = serializers.BooleanField(source="medication.is_high_alert", read_only=True)

    class Meta:
        model = Prescription
        fields = [
            "id",
            "prescription_number",
            "patient",
            "patient_name",
            "medication",
            "medication_name",
            "dose_quantity",
            "dose_unit",
            "frequency",
            "status",
            "priority",
            "start_date",
            "end_date",
            "is_high_alert",
            "prescribed_at",
        ]

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating prescriptions."""

    class Meta:
        model = Prescription
        fields = [
            "patient",
            "medication",
            "dose_quantity",
            "dose_unit",
            "route",
            "frequency",
            "frequency_hours",
            "start_date",
            "end_date",
            "duration_days",
            "quantity_prescribed",
            "refills_allowed",
            "prn_reason",
            "max_prn_doses_per_day",
            "indication",
            "diagnosis_codes",
            "special_instructions",
            "prescriber_name",
            "prescriber_id",
            "prescriber_npi",
            "priority",
        ]


class MedicationAdministrationSerializer(serializers.ModelSerializer):
    """Serializer for medication administrations."""

    prescription_number = serializers.CharField(source="prescription.prescription_number", read_only=True)
    medication_name = serializers.CharField(source="prescription.medication.generic_name", read_only=True)
    patient_name = serializers.SerializerMethodField()
    is_high_alert = serializers.BooleanField(source="prescription.medication.is_high_alert", read_only=True)

    class Meta:
        model = MedicationAdministration
        fields = [
            "id",
            "prescription",
            "prescription_number",
            "medication_name",
            "patient_name",
            "fhir_id",
            "scheduled_time",
            "status",
            "administered_at",
            "administered_by",
            "administered_by_id",
            "dose_given",
            "dose_unit",
            "route_given",
            "site",
            "not_given_reason",
            "not_given_details",
            "witness_name",
            "witness_id",
            "patient_response",
            "vital_signs_before",
            "vital_signs_after",
            "notes",
            "is_high_alert",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_patient_name(self, obj):
        patient = obj.prescription.patient
        return f"{patient.first_name} {patient.last_name}"


class MedicationAdministrationListSerializer(serializers.ModelSerializer):
    """Compact serializer for MAR lists."""

    medication_name = serializers.CharField(source="prescription.medication.generic_name", read_only=True)
    patient_name = serializers.SerializerMethodField()
    is_high_alert = serializers.BooleanField(source="prescription.medication.is_high_alert", read_only=True)

    class Meta:
        model = MedicationAdministration
        fields = [
            "id",
            "prescription",
            "medication_name",
            "patient_name",
            "scheduled_time",
            "status",
            "administered_at",
            "administered_by",
            "dose_given",
            "is_high_alert",
        ]

    def get_patient_name(self, obj):
        patient = obj.prescription.patient
        return f"{patient.first_name} {patient.last_name}"
