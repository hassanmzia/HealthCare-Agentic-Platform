from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from patients.models import Patient
import uuid


class Encounter(models.Model):
    """Clinical encounter/visit for a patient."""

    ENCOUNTER_TYPES = [
        ("ambulatory", "Ambulatory Visit"),
        ("emergency", "Emergency Visit"),
        ("inpatient", "Inpatient Stay"),
        ("observation", "Observation"),
        ("telehealth", "Telehealth"),
        ("home_health", "Home Health"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("in_progress", "In Progress"),
        ("on_hold", "On Hold"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    PRIORITY_CHOICES = [
        ("routine", "Routine"),
        ("urgent", "Urgent"),
        ("emergency", "Emergency"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="encounters")
    fhir_id = models.CharField(max_length=100, blank=True, null=True, help_text="FHIR Encounter resource ID")

    encounter_type = models.CharField(max_length=50, choices=ENCOUNTER_TYPES, default="ambulatory")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="in_progress")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="routine")

    # Timing
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)

    # Location
    facility = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=200, blank=True)
    room = models.CharField(max_length=50, blank=True)
    bed = models.CharField(max_length=50, blank=True)

    # Provider
    attending_physician = models.CharField(max_length=200, blank=True)
    attending_physician_id = models.CharField(max_length=100, blank=True)

    # Chief Complaint
    chief_complaint = models.TextField(blank=True, help_text="Primary reason for visit")
    reason_codes = models.JSONField(default=list, blank=True, help_text="ICD-10 codes for reason")

    # Notes
    notes = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_time"]
        verbose_name = "Encounter"
        verbose_name_plural = "Encounters"

    def __str__(self):
        return f"{self.encounter_type} - {self.patient.full_name} ({self.start_time.date()})"


class ClinicalNote(models.Model):
    """Clinical documentation for patient encounters."""

    NOTE_TYPES = [
        ("progress", "Progress Note"),
        ("admission", "Admission Note"),
        ("discharge", "Discharge Summary"),
        ("consultation", "Consultation Note"),
        ("procedure", "Procedure Note"),
        ("nursing", "Nursing Note"),
        ("soap", "SOAP Note"),
        ("history_physical", "History & Physical"),
        ("referral", "Referral Note"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("final", "Final"),
        ("amended", "Amended"),
        ("entered_in_error", "Entered in Error"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="clinical_notes")
    encounter = models.ForeignKey(Encounter, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinical_notes")

    note_type = models.CharField(max_length=50, choices=NOTE_TYPES, default="progress")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    title = models.CharField(max_length=255)

    # SOAP Note Structure
    subjective = models.TextField(blank=True, help_text="Patient's symptoms and complaints")
    objective = models.TextField(blank=True, help_text="Physical exam and test results")
    assessment = models.TextField(blank=True, help_text="Diagnoses and clinical impressions")
    plan = models.TextField(blank=True, help_text="Treatment plan and next steps")

    # General content (for non-SOAP notes)
    content = models.TextField(blank=True, help_text="Full note content")

    # Provider
    author = models.CharField(max_length=200)
    author_role = models.CharField(max_length=100, blank=True, help_text="e.g., MD, NP, RN")
    co_signer = models.CharField(max_length=200, blank=True)

    # Timestamps
    note_datetime = models.DateTimeField(help_text="When the note was recorded")
    signed_datetime = models.DateTimeField(blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-note_datetime"]
        verbose_name = "Clinical Note"
        verbose_name_plural = "Clinical Notes"

    def __str__(self):
        return f"{self.note_type}: {self.title} - {self.patient.full_name}"


class Diagnosis(models.Model):
    """Patient diagnoses with ICD-10 coding."""

    CATEGORY_CHOICES = [
        ("admitting", "Admitting Diagnosis"),
        ("working", "Working Diagnosis"),
        ("final", "Final Diagnosis"),
        ("discharge", "Discharge Diagnosis"),
        ("billing", "Billing Diagnosis"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("resolved", "Resolved"),
        ("inactive", "Inactive"),
        ("ruled_out", "Ruled Out"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="diagnoses")
    encounter = models.ForeignKey(Encounter, on_delete=models.SET_NULL, null=True, blank=True, related_name="diagnoses")

    # ICD-10 Code
    icd10_code = models.CharField(max_length=20, help_text="ICD-10 diagnosis code")
    description = models.CharField(max_length=500, help_text="Diagnosis description")

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="working")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # Clinical details
    onset_date = models.DateField(blank=True, null=True)
    resolution_date = models.DateField(blank=True, null=True)
    severity = models.CharField(max_length=50, blank=True, help_text="e.g., mild, moderate, severe")
    clinical_notes = models.TextField(blank=True)

    # Provider
    diagnosed_by = models.CharField(max_length=200, blank=True)
    diagnosed_date = models.DateTimeField(auto_now_add=True)

    # Ranking for billing
    is_primary = models.BooleanField(default=False, help_text="Primary diagnosis for encounter")
    rank = models.IntegerField(default=1, help_text="Order of diagnosis")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["rank", "-created_at"]
        verbose_name = "Diagnosis"
        verbose_name_plural = "Diagnoses"

    def __str__(self):
        return f"{self.icd10_code}: {self.description} - {self.patient.full_name}"


class CarePlan(models.Model):
    """Care plan for patient treatment."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("on_hold", "On Hold"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    CATEGORY_CHOICES = [
        ("assessment", "Assessment & Plan"),
        ("treatment", "Treatment Plan"),
        ("discharge", "Discharge Plan"),
        ("follow_up", "Follow-up Plan"),
        ("chronic", "Chronic Care Management"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="care_plans")
    encounter = models.ForeignKey(Encounter, on_delete=models.SET_NULL, null=True, blank=True, related_name="care_plans")

    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="treatment")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # Care plan details
    description = models.TextField(blank=True)
    goals = models.JSONField(default=list, blank=True, help_text="List of care goals")
    activities = models.JSONField(default=list, blank=True, help_text="List of planned activities")

    # Timing
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    # Related diagnoses
    addresses_diagnoses = models.ManyToManyField(Diagnosis, blank=True, related_name="care_plans")

    # Provider
    created_by = models.CharField(max_length=200)
    care_team = models.JSONField(default=list, blank=True, help_text="Care team members")

    # Instructions
    patient_instructions = models.TextField(blank=True, help_text="Instructions for patient")
    follow_up_instructions = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Care Plan"
        verbose_name_plural = "Care Plans"

    def __str__(self):
        return f"{self.title} - {self.patient.full_name}"


class Vitals(models.Model):
    """Vital signs recorded during encounters."""

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="vitals_records")
    encounter = models.ForeignKey(Encounter, on_delete=models.SET_NULL, null=True, blank=True, related_name="vitals")

    # Vital signs
    heart_rate = models.IntegerField(blank=True, null=True, help_text="bpm")
    blood_pressure_systolic = models.IntegerField(blank=True, null=True, help_text="mmHg")
    blood_pressure_diastolic = models.IntegerField(blank=True, null=True, help_text="mmHg")
    respiratory_rate = models.IntegerField(blank=True, null=True, help_text="breaths/min")
    temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True, help_text="Celsius")
    oxygen_saturation = models.IntegerField(blank=True, null=True, help_text="SpO2 %")
    weight = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, help_text="kg")
    height = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, help_text="cm")
    bmi = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    pain_level = models.IntegerField(blank=True, null=True, help_text="0-10 scale")

    # Recording info
    recorded_at = models.DateTimeField()
    recorded_by = models.CharField(max_length=200, blank=True)
    method = models.CharField(max_length=100, blank=True, help_text="Manual, device, etc.")
    device_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]
        verbose_name = "Vitals Record"
        verbose_name_plural = "Vitals Records"

    def __str__(self):
        return f"Vitals - {self.patient.full_name} ({self.recorded_at})"

    @property
    def blood_pressure(self):
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None


# =============================================================================
# AI Clinical Assessment Models
# =============================================================================

class ClinicalAssessment(models.Model):
    """
    Stores AI-generated clinical assessments for physician review.
    This is the primary record of the multi-agent clinical analysis.
    """

    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("in_review", "In Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("modified", "Modified & Approved"),
        ("expired", "Expired"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="clinical_assessments")
    encounter = models.ForeignKey(Encounter, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinical_assessments")

    # Assessment Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Patient Context at time of assessment
    patient_summary = models.JSONField(default=dict, help_text="Patient demographics and summary at assessment time")
    chief_complaint = models.TextField(blank=True)
    history_present_illness = models.TextField(blank=True)
    physician_notes = models.TextField(blank=True, help_text="Pre-assessment physician notes")

    # AI-Generated Findings
    findings = models.JSONField(default=list, help_text="List of clinical findings")
    critical_findings = models.JSONField(default=list, help_text="Critical findings requiring attention")

    # Diagnoses
    diagnoses = models.JSONField(default=list, help_text="AI-recommended diagnoses with ICD-10 codes")
    primary_diagnosis_code = models.CharField(max_length=20, blank=True, help_text="Primary ICD-10 code")
    primary_diagnosis_description = models.CharField(max_length=500, blank=True)

    # Treatments
    treatments = models.JSONField(default=list, help_text="AI-recommended treatments with CPT codes")
    immediate_actions = models.JSONField(default=list, help_text="Urgent actions required")

    # Coding
    icd10_codes = models.JSONField(default=list, help_text="All ICD-10 codes")
    cpt_codes = models.JSONField(default=list, help_text="All CPT codes")

    # AI Metadata
    confidence_score = models.FloatField(default=0.0, help_text="Overall confidence 0-1")
    reasoning_chain = models.JSONField(default=list, help_text="AI reasoning steps")
    warnings = models.JSONField(default=list, help_text="Warnings and alerts")
    agents_used = models.JSONField(default=list, help_text="List of specialist agents invoked")

    # Review Requirements
    requires_human_review = models.BooleanField(default=True)
    review_reasons = models.JSONField(default=list, help_text="Reasons review is required")

    # LLM Provider Info
    llm_provider = models.CharField(max_length=50, blank=True, help_text="LLM provider used (claude, ollama)")

    # Timestamps
    assessment_datetime = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(blank=True, null=True, help_text="Assessment validity expiration")

    class Meta:
        ordering = ["-assessment_datetime"]
        verbose_name = "Clinical Assessment"
        verbose_name_plural = "Clinical Assessments"
        indexes = [
            models.Index(fields=["patient", "-assessment_datetime"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"Assessment {self.id} - {self.patient.full_name} ({self.assessment_datetime.date()})"

    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class PhysicianReview(models.Model):
    """
    Records physician review and sign-off on AI clinical assessments.
    Supports approval, rejection, and modification workflows.
    """

    DECISION_CHOICES = [
        ("approved", "Approved"),
        ("approved_modified", "Approved with Modifications"),
        ("rejected", "Rejected"),
        ("deferred", "Deferred for Further Review"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(ClinicalAssessment, on_delete=models.CASCADE, related_name="physician_reviews")

    # Physician Info
    physician_id = models.CharField(max_length=100, help_text="Physician user ID")
    physician_name = models.CharField(max_length=200)
    physician_npi = models.CharField(max_length=20, blank=True, help_text="National Provider Identifier")
    physician_specialty = models.CharField(max_length=100, blank=True)

    # Review Decision
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)

    # Approved/Rejected Items
    approved_diagnoses = models.JSONField(default=list, help_text="Indices of approved diagnoses")
    rejected_diagnoses = models.JSONField(default=list, help_text="Indices of rejected diagnoses")
    approved_treatments = models.JSONField(default=list, help_text="Indices of approved treatments")
    rejected_treatments = models.JSONField(default=list, help_text="Indices of rejected treatments")

    # Modifications
    modified_diagnoses = models.JSONField(default=list, help_text="Modified diagnosis entries")
    modified_treatments = models.JSONField(default=list, help_text="Modified treatment entries")
    added_diagnoses = models.JSONField(default=list, help_text="Physician-added diagnoses")
    added_treatments = models.JSONField(default=list, help_text="Physician-added treatments")

    # Final Codes after review
    final_icd10_codes = models.JSONField(default=list, help_text="Final approved ICD-10 codes")
    final_cpt_codes = models.JSONField(default=list, help_text="Final approved CPT codes")

    # Clinical Notes
    physician_notes = models.TextField(blank=True, help_text="Physician's review notes")
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection if rejected")
    clinical_rationale = models.TextField(blank=True, help_text="Clinical rationale for modifications")

    # Attestation
    attestation_statement = models.TextField(
        default="I have reviewed this AI-generated clinical assessment and confirm that "
                "my review represents my independent clinical judgment.",
        help_text="Attestation statement for medical-legal purposes"
    )
    attested = models.BooleanField(default=False)

    # Digital Signature
    digital_signature = models.CharField(max_length=500, blank=True, help_text="Digital signature hash")
    signature_datetime = models.DateTimeField(blank=True, null=True)

    # Review Timing
    review_started_at = models.DateTimeField(blank=True, null=True)
    review_completed_at = models.DateTimeField(blank=True, null=True)
    time_spent_seconds = models.IntegerField(default=0, help_text="Time spent reviewing in seconds")

    # Metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Physician Review"
        verbose_name_plural = "Physician Reviews"
        indexes = [
            models.Index(fields=["assessment"]),
            models.Index(fields=["physician_id"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"Review by {self.physician_name} - {self.decision} ({self.created_at.date()})"


class AssessmentAuditLog(models.Model):
    """
    Comprehensive audit trail for all assessment-related actions.
    Maintains full traceability for compliance and quality assurance.
    """

    ACTION_TYPES = [
        ("created", "Assessment Created"),
        ("viewed", "Assessment Viewed"),
        ("review_started", "Review Started"),
        ("review_completed", "Review Completed"),
        ("approved", "Assessment Approved"),
        ("rejected", "Assessment Rejected"),
        ("modified", "Assessment Modified"),
        ("diagnosis_approved", "Diagnosis Approved"),
        ("diagnosis_rejected", "Diagnosis Rejected"),
        ("diagnosis_added", "Diagnosis Added"),
        ("diagnosis_modified", "Diagnosis Modified"),
        ("treatment_approved", "Treatment Approved"),
        ("treatment_rejected", "Treatment Rejected"),
        ("treatment_added", "Treatment Added"),
        ("treatment_modified", "Treatment Modified"),
        ("documentation_generated", "Documentation Generated"),
        ("order_placed", "Order Placed to EHR"),
        ("exported", "Assessment Exported"),
        ("expired", "Assessment Expired"),
        ("reopened", "Assessment Reopened"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(ClinicalAssessment, on_delete=models.CASCADE, related_name="audit_logs")
    physician_review = models.ForeignKey(PhysicianReview, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")

    # Action Details
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    action_detail = models.TextField(blank=True, help_text="Detailed description of action")

    # Actor
    actor_id = models.CharField(max_length=100, help_text="User ID who performed action")
    actor_name = models.CharField(max_length=200)
    actor_role = models.CharField(max_length=100, blank=True, help_text="e.g., physician, nurse, system")

    # Before/After State
    previous_state = models.JSONField(default=dict, blank=True, help_text="State before action")
    new_state = models.JSONField(default=dict, blank=True, help_text="State after action")

    # Context
    related_item_type = models.CharField(max_length=50, blank=True, help_text="e.g., diagnosis, treatment")
    related_item_id = models.CharField(max_length=100, blank=True)
    related_item_detail = models.JSONField(default=dict, blank=True)

    # Technical Metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=500, blank=True)
    session_id = models.CharField(max_length=100, blank=True)

    # Timestamp
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Assessment Audit Log"
        verbose_name_plural = "Assessment Audit Logs"
        indexes = [
            models.Index(fields=["assessment", "-timestamp"]),
            models.Index(fields=["actor_id"]),
            models.Index(fields=["action"]),
            models.Index(fields=["-timestamp"]),
        ]

    def __str__(self):
        return f"{self.action} by {self.actor_name} ({self.timestamp})"


class ClinicalDocument(models.Model):
    """
    Generated clinical documentation from approved assessments.
    Supports various document types for EHR integration and record keeping.
    """

    DOCUMENT_TYPES = [
        ("assessment_summary", "Assessment Summary"),
        ("progress_note", "Progress Note"),
        ("discharge_summary", "Discharge Summary"),
        ("referral_letter", "Referral Letter"),
        ("order_summary", "Order Summary"),
        ("consultation_note", "Consultation Note"),
        ("care_plan", "Care Plan Document"),
    ]

    FORMAT_CHOICES = [
        ("html", "HTML"),
        ("pdf", "PDF"),
        ("fhir", "FHIR Document"),
        ("ccd", "CCD (HL7 CDA)"),
        ("plain_text", "Plain Text"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("final", "Final"),
        ("amended", "Amended"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(ClinicalAssessment, on_delete=models.CASCADE, related_name="documents")
    physician_review = models.ForeignKey(PhysicianReview, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")

    # Document Info
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=255)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default="html")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Content
    content = models.TextField(help_text="Document content (HTML, text, etc.)")
    structured_data = models.JSONField(default=dict, blank=True, help_text="Structured data for FHIR/CCD")

    # File Storage (if PDF)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.IntegerField(default=0)

    # Author
    generated_by = models.CharField(max_length=100, help_text="System or user who generated")
    signed_by = models.CharField(max_length=200, blank=True)
    signed_at = models.DateTimeField(blank=True, null=True)

    # Versioning
    version = models.IntegerField(default=1)
    parent_document = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name="amendments")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Clinical Document"
        verbose_name_plural = "Clinical Documents"

    def __str__(self):
        return f"{self.document_type}: {self.title}"


class EHROrder(models.Model):
    """
    Tracks orders placed to the EHR system from approved assessments.
    Supports medication orders, lab orders, imaging orders, and referrals.
    """

    ORDER_TYPES = [
        ("medication", "Medication Order"),
        ("lab", "Laboratory Order"),
        ("imaging", "Imaging Order"),
        ("procedure", "Procedure Order"),
        ("referral", "Referral Order"),
        ("consultation", "Consultation Order"),
        ("diet", "Diet Order"),
        ("activity", "Activity Order"),
        ("nursing", "Nursing Order"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("submitted", "Submitted to EHR"),
        ("accepted", "Accepted by EHR"),
        ("rejected", "Rejected by EHR"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("error", "Error"),
    ]

    PRIORITY_CHOICES = [
        ("routine", "Routine"),
        ("urgent", "Urgent"),
        ("stat", "STAT"),
        ("asap", "ASAP"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(ClinicalAssessment, on_delete=models.CASCADE, related_name="ehr_orders")
    physician_review = models.ForeignKey(PhysicianReview, on_delete=models.SET_NULL, null=True, blank=True, related_name="ehr_orders")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="ehr_orders")

    # Order Details
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="routine")

    # Order Content
    description = models.TextField()
    cpt_code = models.CharField(max_length=20, blank=True)
    order_details = models.JSONField(default=dict, help_text="Structured order details")

    # For Medications
    medication_name = models.CharField(max_length=200, blank=True)
    medication_dose = models.CharField(max_length=100, blank=True)
    medication_route = models.CharField(max_length=50, blank=True)
    medication_frequency = models.CharField(max_length=100, blank=True)
    medication_duration = models.CharField(max_length=100, blank=True)

    # For Labs/Imaging
    test_name = models.CharField(max_length=200, blank=True)
    test_code = models.CharField(max_length=50, blank=True)
    specimen_type = models.CharField(max_length=100, blank=True)
    body_site = models.CharField(max_length=100, blank=True)

    # For Referrals
    referral_specialty = models.CharField(max_length=100, blank=True)
    referral_reason = models.TextField(blank=True)
    referral_urgency = models.CharField(max_length=50, blank=True)

    # Clinical Indication
    indication = models.TextField(blank=True, help_text="Clinical indication for order")
    icd10_codes = models.JSONField(default=list, help_text="Supporting diagnosis codes")

    # Ordering Provider
    ordering_physician_id = models.CharField(max_length=100)
    ordering_physician_name = models.CharField(max_length=200)
    ordering_physician_npi = models.CharField(max_length=20, blank=True)

    # EHR Integration
    ehr_system = models.CharField(max_length=50, blank=True, help_text="Target EHR system")
    ehr_order_id = models.CharField(max_length=100, blank=True, help_text="Order ID in EHR")
    ehr_response = models.JSONField(default=dict, blank=True, help_text="Response from EHR")

    # Submission Tracking
    submitted_at = models.DateTimeField(blank=True, null=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "EHR Order"
        verbose_name_plural = "EHR Orders"
        indexes = [
            models.Index(fields=["patient", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["order_type"]),
        ]

    def __str__(self):
        return f"{self.order_type}: {self.description[:50]} - {self.status}"
