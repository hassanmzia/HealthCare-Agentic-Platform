from rest_framework import serializers
from .models import (
    Encounter, ClinicalNote, Diagnosis, CarePlan, Vitals,
    ClinicalAssessment, PhysicianReview, AssessmentAuditLog,
    ClinicalDocument, EHROrder
)


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


# =============================================================================
# AI Clinical Assessment Serializers
# =============================================================================

class ClinicalAssessmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for assessment lists."""
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    patient_mrn = serializers.CharField(source="patient.mrn", read_only=True)
    critical_count = serializers.SerializerMethodField()
    diagnosis_count = serializers.SerializerMethodField()

    class Meta:
        model = ClinicalAssessment
        fields = [
            "id", "patient", "patient_name", "patient_mrn", "encounter",
            "status", "primary_diagnosis_description", "primary_diagnosis_code",
            "confidence_score", "requires_human_review",
            "critical_count", "diagnosis_count",
            "assessment_datetime", "created_at"
        ]

    def get_critical_count(self, obj):
        return len(obj.critical_findings) if obj.critical_findings else 0

    def get_diagnosis_count(self, obj):
        return len(obj.diagnoses) if obj.diagnoses else 0


class ClinicalAssessmentDetailSerializer(serializers.ModelSerializer):
    """Full serializer for assessment details."""
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    patient_mrn = serializers.CharField(source="patient.mrn", read_only=True)
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = ClinicalAssessment
        fields = [
            "id", "patient", "patient_name", "patient_mrn", "encounter",
            "status", "patient_summary", "chief_complaint",
            "history_present_illness", "physician_notes",
            "findings", "critical_findings",
            "diagnoses", "primary_diagnosis_code", "primary_diagnosis_description",
            "treatments", "immediate_actions",
            "icd10_codes", "cpt_codes",
            "confidence_score", "reasoning_chain", "warnings", "agents_used",
            "requires_human_review", "review_reasons",
            "llm_provider", "assessment_datetime", "expires_at",
            "reviews", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_reviews(self, obj):
        reviews = obj.physician_reviews.all().order_by('-created_at')[:5]
        return PhysicianReviewListSerializer(reviews, many=True).data


class ClinicalAssessmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating assessments from the orchestrator."""

    class Meta:
        model = ClinicalAssessment
        fields = [
            "patient", "encounter", "patient_summary", "chief_complaint",
            "history_present_illness", "physician_notes",
            "findings", "critical_findings",
            "diagnoses", "primary_diagnosis_code", "primary_diagnosis_description",
            "treatments", "immediate_actions",
            "icd10_codes", "cpt_codes",
            "confidence_score", "reasoning_chain", "warnings", "agents_used",
            "requires_human_review", "review_reasons", "llm_provider"
        ]


class PhysicianReviewListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for review lists."""

    class Meta:
        model = PhysicianReview
        fields = [
            "id", "assessment", "physician_id", "physician_name",
            "decision", "attested", "review_completed_at",
            "time_spent_seconds", "created_at"
        ]


class PhysicianReviewDetailSerializer(serializers.ModelSerializer):
    """Full serializer for physician review details."""

    class Meta:
        model = PhysicianReview
        fields = [
            "id", "assessment",
            "physician_id", "physician_name", "physician_npi", "physician_specialty",
            "decision",
            "approved_diagnoses", "rejected_diagnoses",
            "approved_treatments", "rejected_treatments",
            "modified_diagnoses", "modified_treatments",
            "added_diagnoses", "added_treatments",
            "final_icd10_codes", "final_cpt_codes",
            "physician_notes", "rejection_reason", "clinical_rationale",
            "attestation_statement", "attested",
            "signature_datetime",
            "review_started_at", "review_completed_at", "time_spent_seconds",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PhysicianReviewSubmitSerializer(serializers.Serializer):
    """Serializer for submitting a physician review."""
    assessment_id = serializers.UUIDField()
    physician_id = serializers.CharField(max_length=100)
    physician_name = serializers.CharField(max_length=200)
    physician_npi = serializers.CharField(max_length=20, required=False, allow_blank=True)
    physician_specialty = serializers.CharField(max_length=100, required=False, allow_blank=True)

    decision = serializers.ChoiceField(choices=[
        ("approved", "Approved"),
        ("approved_modified", "Approved with Modifications"),
        ("rejected", "Rejected"),
        ("deferred", "Deferred"),
    ])

    approved_diagnoses = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    rejected_diagnoses = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    approved_treatments = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    rejected_treatments = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)

    modified_diagnoses = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    modified_treatments = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    added_diagnoses = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    added_treatments = serializers.ListField(child=serializers.DictField(), required=False, default=list)

    physician_notes = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    clinical_rationale = serializers.CharField(required=False, allow_blank=True)

    attest = serializers.BooleanField(default=False)
    review_started_at = serializers.DateTimeField(required=False, allow_null=True)


class AssessmentAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit log entries."""

    class Meta:
        model = AssessmentAuditLog
        fields = [
            "id", "assessment", "physician_review",
            "action", "action_detail",
            "actor_id", "actor_name", "actor_role",
            "previous_state", "new_state",
            "related_item_type", "related_item_id", "related_item_detail",
            "ip_address", "timestamp"
        ]
        read_only_fields = ["id", "timestamp"]


class ClinicalDocumentSerializer(serializers.ModelSerializer):
    """Serializer for clinical documents."""

    class Meta:
        model = ClinicalDocument
        fields = [
            "id", "assessment", "physician_review",
            "document_type", "title", "format", "status",
            "content", "structured_data",
            "file_path", "file_size",
            "generated_by", "signed_by", "signed_at",
            "version", "parent_document",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EHROrderSerializer(serializers.ModelSerializer):
    """Serializer for EHR orders."""
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = EHROrder
        fields = [
            "id", "assessment", "physician_review", "patient", "patient_name",
            "order_type", "status", "priority",
            "description", "cpt_code", "order_details",
            "medication_name", "medication_dose", "medication_route",
            "medication_frequency", "medication_duration",
            "test_name", "test_code", "specimen_type", "body_site",
            "referral_specialty", "referral_reason", "referral_urgency",
            "indication", "icd10_codes",
            "ordering_physician_id", "ordering_physician_name", "ordering_physician_npi",
            "ehr_system", "ehr_order_id", "ehr_response",
            "submitted_at", "accepted_at", "completed_at",
            "error_message", "retry_count",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EHROrderCreateSerializer(serializers.Serializer):
    """Serializer for creating EHR orders from approved treatments."""
    assessment_id = serializers.UUIDField()
    review_id = serializers.UUIDField()
    treatment_indices = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="Indices of treatments to create orders for"
    )
    ordering_physician_id = serializers.CharField(max_length=100)
    ordering_physician_name = serializers.CharField(max_length=200)
    ordering_physician_npi = serializers.CharField(max_length=20, required=False, allow_blank=True)


class DocumentGenerateSerializer(serializers.Serializer):
    """Serializer for generating clinical documents."""
    assessment_id = serializers.UUIDField()
    review_id = serializers.UUIDField(required=False, allow_null=True)
    document_type = serializers.ChoiceField(choices=[
        ("assessment_summary", "Assessment Summary"),
        ("progress_note", "Progress Note"),
        ("discharge_summary", "Discharge Summary"),
        ("referral_letter", "Referral Letter"),
        ("order_summary", "Order Summary"),
    ])
    format = serializers.ChoiceField(
        choices=[("html", "HTML"), ("pdf", "PDF"), ("plain_text", "Plain Text")],
        default="html"
    )
    include_reasoning = serializers.BooleanField(default=False)
    include_codes = serializers.BooleanField(default=True)
