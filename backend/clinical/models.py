from django.db import models
from patients.models import Patient


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
