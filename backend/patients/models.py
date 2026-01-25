from django.db import models
from django.core.validators import RegexValidator


class Patient(models.Model):
    """Comprehensive Patient model for EHR management."""

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
        ("unknown", "Unknown"),
    ]

    BLOOD_TYPE_CHOICES = [
        ("A+", "A+"), ("A-", "A-"),
        ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"),
        ("O+", "O+"), ("O-", "O-"),
        ("unknown", "Unknown"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("deceased", "Deceased"),
    ]

    # Basic Information
    mrn = models.CharField(max_length=50, unique=True, verbose_name="Medical Record Number")
    fhir_id = models.CharField(max_length=100, blank=True, null=True, help_text="FHIR Patient resource ID")

    # Name
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    prefix = models.CharField(max_length=20, blank=True, help_text="e.g., Mr., Mrs., Dr.")
    suffix = models.CharField(max_length=20, blank=True, help_text="e.g., Jr., Sr., III")

    # Demographics
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default="unknown")
    blood_type = models.CharField(max_length=10, choices=BLOOD_TYPE_CHOICES, default="unknown")
    ssn = models.CharField(max_length=11, blank=True, verbose_name="SSN", help_text="XXX-XX-XXXX")

    # Contact Information
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number format: '+999999999'")
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    phone_secondary = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    email = models.EmailField(blank=True)

    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default="USA")

    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=17, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)

    # Insurance Information
    insurance_provider = models.CharField(max_length=200, blank=True)
    insurance_policy_number = models.CharField(max_length=100, blank=True)
    insurance_group_number = models.CharField(max_length=100, blank=True)

    # Medical Information
    allergies = models.JSONField(default=list, blank=True, help_text="List of allergies")
    medications = models.JSONField(default=list, blank=True, help_text="Current medications")
    medical_conditions = models.JSONField(default=list, blank=True, help_text="Chronic conditions")
    medical_history = models.TextField(blank=True, help_text="Additional medical history notes")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    primary_care_physician = models.CharField(max_length=200, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):
        return f"{self.last_name}, {self.first_name} (MRN: {self.mrn})"

    @property
    def full_name(self):
        parts = [self.prefix, self.first_name, self.middle_name, self.last_name, self.suffix]
        return " ".join(p for p in parts if p)

    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class PatientDocument(models.Model):
    """Documents associated with a patient (X-rays, lab reports, etc.)."""

    DOCUMENT_TYPES = [
        ("xray", "X-Ray"),
        ("ct_scan", "CT Scan"),
        ("mri", "MRI"),
        ("lab_report", "Lab Report"),
        ("pathology", "Pathology Report"),
        ("prescription", "Prescription"),
        ("referral", "Referral"),
        ("consent", "Consent Form"),
        ("other", "Other"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file_url = models.URLField(blank=True, help_text="URL to the document/image")
    file_data = models.TextField(blank=True, help_text="Base64 encoded file data for small files")
    mime_type = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.document_type}: {self.title} - {self.patient}"
