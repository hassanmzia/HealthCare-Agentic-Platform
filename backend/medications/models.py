from django.db import models
from patients.models import Patient


class MedicationCatalog(models.Model):
    """Drug catalog with standard medication information."""

    ROUTE_CHOICES = [
        ("oral", "Oral"),
        ("iv", "Intravenous (IV)"),
        ("im", "Intramuscular (IM)"),
        ("subq", "Subcutaneous"),
        ("topical", "Topical"),
        ("inhalation", "Inhalation"),
        ("rectal", "Rectal"),
        ("ophthalmic", "Ophthalmic"),
        ("otic", "Otic (Ear)"),
        ("nasal", "Nasal"),
        ("sublingual", "Sublingual"),
        ("transdermal", "Transdermal"),
        ("other", "Other"),
    ]

    FORM_CHOICES = [
        ("tablet", "Tablet"),
        ("capsule", "Capsule"),
        ("liquid", "Liquid/Solution"),
        ("injection", "Injection"),
        ("cream", "Cream/Ointment"),
        ("patch", "Patch"),
        ("inhaler", "Inhaler"),
        ("drops", "Drops"),
        ("suppository", "Suppository"),
        ("powder", "Powder"),
        ("spray", "Spray"),
        ("other", "Other"),
    ]

    CATEGORY_CHOICES = [
        ("analgesic", "Analgesics/Pain Relief"),
        ("antibiotic", "Antibiotics"),
        ("antihypertensive", "Antihypertensives"),
        ("antidiabetic", "Antidiabetics"),
        ("anticoagulant", "Anticoagulants"),
        ("cardiovascular", "Cardiovascular"),
        ("respiratory", "Respiratory"),
        ("gastrointestinal", "Gastrointestinal"),
        ("psychiatric", "Psychiatric/Neurological"),
        ("endocrine", "Endocrine/Hormones"),
        ("antiinflammatory", "Anti-inflammatory"),
        ("immunosuppressant", "Immunosuppressants"),
        ("vitamin", "Vitamins/Supplements"),
        ("other", "Other"),
    ]

    # Drug identification
    rxnorm_code = models.CharField(max_length=20, unique=True, help_text="RxNorm code")
    ndc_code = models.CharField(max_length=20, blank=True, help_text="NDC code")
    generic_name = models.CharField(max_length=200)
    brand_names = models.JSONField(default=list, help_text="List of brand names")

    # Classification
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    drug_class = models.CharField(max_length=100, blank=True, help_text="Pharmacological class")

    # Form and administration
    form = models.CharField(max_length=50, choices=FORM_CHOICES)
    route = models.CharField(max_length=50, choices=ROUTE_CHOICES)
    strength = models.CharField(max_length=100, help_text="e.g., 500mg, 10mg/5mL")
    unit = models.CharField(max_length=50, help_text="Unit of measure")

    # Dosing information
    typical_dose_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    typical_dose_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_daily_dose = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    frequency_options = models.JSONField(default=list, help_text="Common frequencies")

    # Safety information
    contraindications = models.TextField(blank=True)
    warnings = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)

    # Flags
    is_controlled = models.BooleanField(default=False)
    controlled_schedule = models.CharField(max_length=10, blank=True, help_text="DEA Schedule (II-V)")
    requires_monitoring = models.BooleanField(default=False)
    monitoring_parameters = models.TextField(blank=True)
    is_high_alert = models.BooleanField(default=False, help_text="High-alert medication")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Medication"
        verbose_name_plural = "Medication Catalog"
        ordering = ["generic_name"]

    def __str__(self):
        return f"{self.generic_name} {self.strength} ({self.form})"


class DrugInteraction(models.Model):
    """Known drug-drug interactions."""

    SEVERITY_CHOICES = [
        ("minor", "Minor"),
        ("moderate", "Moderate"),
        ("major", "Major"),
        ("contraindicated", "Contraindicated"),
    ]

    drug_a = models.ForeignKey(
        MedicationCatalog,
        on_delete=models.CASCADE,
        related_name="interactions_as_drug_a"
    )
    drug_b = models.ForeignKey(
        MedicationCatalog,
        on_delete=models.CASCADE,
        related_name="interactions_as_drug_b"
    )
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField()
    clinical_effects = models.TextField(blank=True)
    management = models.TextField(blank=True, help_text="How to manage this interaction")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["drug_a", "drug_b"]
        ordering = ["-severity", "drug_a__generic_name"]

    def __str__(self):
        return f"{self.drug_a.generic_name} + {self.drug_b.generic_name} ({self.severity})"


class PatientAllergy(models.Model):
    """Patient allergy records for medication safety."""

    SEVERITY_CHOICES = [
        ("mild", "Mild"),
        ("moderate", "Moderate"),
        ("severe", "Severe"),
        ("life_threatening", "Life-Threatening"),
    ]

    REACTION_TYPE_CHOICES = [
        ("allergy", "Allergy"),
        ("intolerance", "Intolerance"),
        ("adverse_reaction", "Adverse Reaction"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="allergies")

    # What they're allergic to
    allergen_type = models.CharField(
        max_length=20,
        choices=[("drug", "Drug"), ("drug_class", "Drug Class"), ("ingredient", "Ingredient")],
        default="drug"
    )
    allergen_name = models.CharField(max_length=200)
    medication = models.ForeignKey(
        MedicationCatalog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Link to specific medication if applicable"
    )

    # Reaction details
    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPE_CHOICES, default="allergy")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    reaction_description = models.TextField(help_text="Description of reaction")
    onset_date = models.DateField(null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    verified = models.BooleanField(default=False)
    verified_by = models.CharField(max_length=200, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Patient Allergy"
        verbose_name_plural = "Patient Allergies"
        ordering = ["-severity", "allergen_name"]

    def __str__(self):
        return f"{self.patient} - {self.allergen_name} ({self.severity})"


class Prescription(models.Model):
    """Medication orders/prescriptions."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending", "Pending Review"),
        ("active", "Active"),
        ("on_hold", "On Hold"),
        ("completed", "Completed"),
        ("discontinued", "Discontinued"),
        ("cancelled", "Cancelled"),
    ]

    PRIORITY_CHOICES = [
        ("routine", "Routine"),
        ("urgent", "Urgent"),
        ("stat", "STAT"),
        ("prn", "PRN (As Needed)"),
    ]

    # Order identification
    prescription_number = models.CharField(max_length=50, unique=True)
    fhir_id = models.CharField(max_length=100, blank=True, help_text="FHIR MedicationRequest ID")

    # Patient and medication
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="prescriptions")
    medication = models.ForeignKey(MedicationCatalog, on_delete=models.PROTECT, related_name="prescriptions")

    # Dosing
    dose_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    dose_unit = models.CharField(max_length=50)
    route = models.CharField(max_length=50)
    frequency = models.CharField(max_length=100, help_text="e.g., BID, TID, Q8H")
    frequency_hours = models.IntegerField(null=True, blank=True, help_text="Hours between doses")

    # Duration
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    duration_days = models.IntegerField(null=True, blank=True)

    # Quantity
    quantity_prescribed = models.IntegerField(null=True, blank=True)
    refills_allowed = models.IntegerField(default=0)
    refills_remaining = models.IntegerField(default=0)

    # PRN details
    prn_reason = models.CharField(max_length=200, blank=True, help_text="Reason for PRN use")
    max_prn_doses_per_day = models.IntegerField(null=True, blank=True)

    # Clinical information
    indication = models.TextField(blank=True, help_text="Reason for prescription")
    diagnosis_codes = models.JSONField(default=list, help_text="ICD-10 codes")
    special_instructions = models.TextField(blank=True)

    # Prescriber
    prescriber_name = models.CharField(max_length=200)
    prescriber_id = models.CharField(max_length=100, blank=True)
    prescriber_npi = models.CharField(max_length=20, blank=True)

    # Status and workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="routine")

    # Pharmacy
    pharmacy_notes = models.TextField(blank=True)
    dispensed_at = models.DateTimeField(null=True, blank=True)
    dispensed_by = models.CharField(max_length=200, blank=True)

    # Safety checks
    allergy_check_passed = models.BooleanField(default=False)
    interaction_check_passed = models.BooleanField(default=False)
    interaction_warnings = models.JSONField(default=list)

    # Hold/discontinue info
    hold_reason = models.TextField(blank=True)
    held_at = models.DateTimeField(null=True, blank=True)
    held_by = models.CharField(max_length=200, blank=True)
    discontinued_reason = models.TextField(blank=True)
    discontinued_at = models.DateTimeField(null=True, blank=True)
    discontinued_by = models.CharField(max_length=200, blank=True)

    # Timestamps
    prescribed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Prescription"
        verbose_name_plural = "Prescriptions"
        ordering = ["-prescribed_at"]
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["prescription_number"]),
            models.Index(fields=["status", "start_date"]),
        ]

    def __str__(self):
        return f"{self.prescription_number}: {self.medication.generic_name} for {self.patient}"


class MedicationAdministration(models.Model):
    """Medication Administration Record (MAR)."""

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("given", "Given"),
        ("not_given", "Not Given"),
        ("refused", "Refused"),
        ("held", "Held"),
        ("missed", "Missed"),
    ]

    NOT_GIVEN_REASONS = [
        ("patient_refused", "Patient Refused"),
        ("patient_unavailable", "Patient Unavailable"),
        ("held_per_protocol", "Held Per Protocol"),
        ("held_per_provider", "Held Per Provider Order"),
        ("npo", "NPO"),
        ("adverse_reaction", "Adverse Reaction"),
        ("medication_unavailable", "Medication Unavailable"),
        ("documentation_error", "Documentation Error"),
        ("other", "Other"),
    ]

    # Links
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name="administrations"
    )
    fhir_id = models.CharField(max_length=100, blank=True, help_text="FHIR MedicationAdministration ID")

    # Scheduling
    scheduled_time = models.DateTimeField()

    # Administration details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    administered_at = models.DateTimeField(null=True, blank=True)
    administered_by = models.CharField(max_length=200, blank=True)
    administered_by_id = models.CharField(max_length=100, blank=True)

    # What was given
    dose_given = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dose_unit = models.CharField(max_length=50, blank=True)
    route_given = models.CharField(max_length=50, blank=True)
    site = models.CharField(max_length=100, blank=True, help_text="Administration site")

    # Not given details
    not_given_reason = models.CharField(max_length=50, choices=NOT_GIVEN_REASONS, blank=True)
    not_given_details = models.TextField(blank=True)

    # Verification
    witness_name = models.CharField(max_length=200, blank=True, help_text="For high-alert meds")
    witness_id = models.CharField(max_length=100, blank=True)

    # Patient response
    patient_response = models.TextField(blank=True)
    vital_signs_before = models.JSONField(default=dict, blank=True)
    vital_signs_after = models.JSONField(default=dict, blank=True)

    # Notes
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Medication Administration"
        verbose_name_plural = "Medication Administrations"
        ordering = ["-scheduled_time"]
        indexes = [
            models.Index(fields=["prescription", "scheduled_time"]),
            models.Index(fields=["status", "scheduled_time"]),
        ]

    def __str__(self):
        return f"{self.prescription.medication.generic_name} @ {self.scheduled_time}"


# Common medications for seeding the catalog
COMMON_MEDICATIONS = [
    # Analgesics
    {"rxnorm_code": "161", "generic_name": "Acetaminophen", "brand_names": ["Tylenol"], "category": "analgesic", "form": "tablet", "route": "oral", "strength": "500mg", "unit": "mg", "frequency_options": ["Q4-6H PRN", "Q6H", "Q8H"]},
    {"rxnorm_code": "5640", "generic_name": "Ibuprofen", "brand_names": ["Advil", "Motrin"], "category": "antiinflammatory", "form": "tablet", "route": "oral", "strength": "400mg", "unit": "mg", "frequency_options": ["Q6H", "Q8H", "TID"]},
    {"rxnorm_code": "7804", "generic_name": "Morphine Sulfate", "brand_names": ["MS Contin"], "category": "analgesic", "form": "injection", "route": "iv", "strength": "4mg/mL", "unit": "mg", "is_controlled": True, "controlled_schedule": "II", "is_high_alert": True, "frequency_options": ["Q4H PRN", "Q2-4H PRN"]},
    {"rxnorm_code": "7052", "generic_name": "Hydrocodone/Acetaminophen", "brand_names": ["Vicodin", "Norco"], "category": "analgesic", "form": "tablet", "route": "oral", "strength": "5/325mg", "unit": "mg", "is_controlled": True, "controlled_schedule": "II", "frequency_options": ["Q4-6H PRN"]},

    # Antibiotics
    {"rxnorm_code": "733", "generic_name": "Amoxicillin", "brand_names": ["Amoxil"], "category": "antibiotic", "form": "capsule", "route": "oral", "strength": "500mg", "unit": "mg", "frequency_options": ["TID", "Q8H"]},
    {"rxnorm_code": "1665005", "generic_name": "Azithromycin", "brand_names": ["Zithromax", "Z-Pack"], "category": "antibiotic", "form": "tablet", "route": "oral", "strength": "250mg", "unit": "mg", "frequency_options": ["Daily", "Day 1: 500mg, Days 2-5: 250mg"]},
    {"rxnorm_code": "2551", "generic_name": "Ciprofloxacin", "brand_names": ["Cipro"], "category": "antibiotic", "form": "tablet", "route": "oral", "strength": "500mg", "unit": "mg", "frequency_options": ["BID", "Q12H"]},
    {"rxnorm_code": "11124", "generic_name": "Vancomycin", "brand_names": ["Vancocin"], "category": "antibiotic", "form": "injection", "route": "iv", "strength": "1g", "unit": "g", "requires_monitoring": True, "monitoring_parameters": "Vancomycin trough levels, renal function", "frequency_options": ["Q12H", "Q8H"]},
    {"rxnorm_code": "1665088", "generic_name": "Ceftriaxone", "brand_names": ["Rocephin"], "category": "antibiotic", "form": "injection", "route": "iv", "strength": "1g", "unit": "g", "frequency_options": ["Daily", "Q12H"]},

    # Antihypertensives
    {"rxnorm_code": "6185", "generic_name": "Lisinopril", "brand_names": ["Zestril", "Prinivil"], "category": "antihypertensive", "form": "tablet", "route": "oral", "strength": "10mg", "unit": "mg", "frequency_options": ["Daily"]},
    {"rxnorm_code": "6918", "generic_name": "Metoprolol Tartrate", "brand_names": ["Lopressor"], "category": "antihypertensive", "form": "tablet", "route": "oral", "strength": "25mg", "unit": "mg", "frequency_options": ["BID", "TID"]},
    {"rxnorm_code": "6918", "generic_name": "Metoprolol Succinate", "brand_names": ["Toprol-XL"], "category": "antihypertensive", "form": "tablet", "route": "oral", "strength": "50mg", "unit": "mg", "frequency_options": ["Daily"]},
    {"rxnorm_code": "321", "generic_name": "Amlodipine", "brand_names": ["Norvasc"], "category": "antihypertensive", "form": "tablet", "route": "oral", "strength": "5mg", "unit": "mg", "frequency_options": ["Daily"]},
    {"rxnorm_code": "5470", "generic_name": "Hydrochlorothiazide", "brand_names": ["Microzide"], "category": "antihypertensive", "form": "tablet", "route": "oral", "strength": "25mg", "unit": "mg", "frequency_options": ["Daily"]},

    # Antidiabetics
    {"rxnorm_code": "6809", "generic_name": "Metformin", "brand_names": ["Glucophage"], "category": "antidiabetic", "form": "tablet", "route": "oral", "strength": "500mg", "unit": "mg", "frequency_options": ["BID", "TID"]},
    {"rxnorm_code": "5856", "generic_name": "Insulin Regular", "brand_names": ["Humulin R", "Novolin R"], "category": "antidiabetic", "form": "injection", "route": "subq", "strength": "100 units/mL", "unit": "units", "is_high_alert": True, "frequency_options": ["Per sliding scale", "TID with meals"]},
    {"rxnorm_code": "274783", "generic_name": "Insulin Glargine", "brand_names": ["Lantus", "Basaglar"], "category": "antidiabetic", "form": "injection", "route": "subq", "strength": "100 units/mL", "unit": "units", "is_high_alert": True, "frequency_options": ["Daily at bedtime", "Daily"]},
    {"rxnorm_code": "1368001", "generic_name": "Empagliflozin", "brand_names": ["Jardiance"], "category": "antidiabetic", "form": "tablet", "route": "oral", "strength": "10mg", "unit": "mg", "frequency_options": ["Daily"]},

    # Anticoagulants
    {"rxnorm_code": "5224", "generic_name": "Heparin", "brand_names": [], "category": "anticoagulant", "form": "injection", "route": "iv", "strength": "1000 units/mL", "unit": "units", "is_high_alert": True, "requires_monitoring": True, "monitoring_parameters": "aPTT, platelets", "frequency_options": ["Continuous infusion", "Q8H", "Q12H"]},
    {"rxnorm_code": "11289", "generic_name": "Warfarin", "brand_names": ["Coumadin"], "category": "anticoagulant", "form": "tablet", "route": "oral", "strength": "5mg", "unit": "mg", "is_high_alert": True, "requires_monitoring": True, "monitoring_parameters": "INR, PT", "frequency_options": ["Daily"]},
    {"rxnorm_code": "1232082", "generic_name": "Apixaban", "brand_names": ["Eliquis"], "category": "anticoagulant", "form": "tablet", "route": "oral", "strength": "5mg", "unit": "mg", "frequency_options": ["BID"]},
    {"rxnorm_code": "67108", "generic_name": "Enoxaparin", "brand_names": ["Lovenox"], "category": "anticoagulant", "form": "injection", "route": "subq", "strength": "40mg/0.4mL", "unit": "mg", "is_high_alert": True, "frequency_options": ["Daily", "BID"]},

    # Cardiovascular
    {"rxnorm_code": "392", "generic_name": "Atorvastatin", "brand_names": ["Lipitor"], "category": "cardiovascular", "form": "tablet", "route": "oral", "strength": "20mg", "unit": "mg", "frequency_options": ["Daily"]},
    {"rxnorm_code": "42463", "generic_name": "Clopidogrel", "brand_names": ["Plavix"], "category": "cardiovascular", "form": "tablet", "route": "oral", "strength": "75mg", "unit": "mg", "frequency_options": ["Daily"]},
    {"rxnorm_code": "4917", "generic_name": "Furosemide", "brand_names": ["Lasix"], "category": "cardiovascular", "form": "tablet", "route": "oral", "strength": "40mg", "unit": "mg", "frequency_options": ["Daily", "BID"]},
    {"rxnorm_code": "4917", "generic_name": "Furosemide IV", "brand_names": ["Lasix"], "category": "cardiovascular", "form": "injection", "route": "iv", "strength": "20mg/2mL", "unit": "mg", "frequency_options": ["Q6H PRN", "Q12H", "Daily"]},

    # Gastrointestinal
    {"rxnorm_code": "7646", "generic_name": "Omeprazole", "brand_names": ["Prilosec"], "category": "gastrointestinal", "form": "capsule", "route": "oral", "strength": "20mg", "unit": "mg", "frequency_options": ["Daily", "BID"]},
    {"rxnorm_code": "8183", "generic_name": "Pantoprazole", "brand_names": ["Protonix"], "category": "gastrointestinal", "form": "tablet", "route": "oral", "strength": "40mg", "unit": "mg", "frequency_options": ["Daily", "BID"]},
    {"rxnorm_code": "7715", "generic_name": "Ondansetron", "brand_names": ["Zofran"], "category": "gastrointestinal", "form": "tablet", "route": "oral", "strength": "4mg", "unit": "mg", "frequency_options": ["Q8H PRN", "Q6H PRN"]},
    {"rxnorm_code": "7715", "generic_name": "Ondansetron IV", "brand_names": ["Zofran"], "category": "gastrointestinal", "form": "injection", "route": "iv", "strength": "4mg/2mL", "unit": "mg", "frequency_options": ["Q8H PRN", "Q6H PRN"]},

    # Psychiatric/Neurological
    {"rxnorm_code": "10582", "generic_name": "Sertraline", "brand_names": ["Zoloft"], "category": "psychiatric", "form": "tablet", "route": "oral", "strength": "50mg", "unit": "mg", "frequency_options": ["Daily"]},
    {"rxnorm_code": "6470", "generic_name": "Lorazepam", "brand_names": ["Ativan"], "category": "psychiatric", "form": "tablet", "route": "oral", "strength": "1mg", "unit": "mg", "is_controlled": True, "controlled_schedule": "IV", "frequency_options": ["Q8H PRN", "BID", "TID"]},
    {"rxnorm_code": "11118", "generic_name": "Trazodone", "brand_names": ["Desyrel"], "category": "psychiatric", "form": "tablet", "route": "oral", "strength": "50mg", "unit": "mg", "frequency_options": ["QHS PRN", "QHS"]},
    {"rxnorm_code": "48937", "generic_name": "Gabapentin", "brand_names": ["Neurontin"], "category": "psychiatric", "form": "capsule", "route": "oral", "strength": "300mg", "unit": "mg", "frequency_options": ["TID", "BID"]},

    # Respiratory
    {"rxnorm_code": "435", "generic_name": "Albuterol", "brand_names": ["Ventolin", "ProAir"], "category": "respiratory", "form": "inhaler", "route": "inhalation", "strength": "90mcg/actuation", "unit": "mcg", "frequency_options": ["Q4-6H PRN", "Q4H PRN"]},
    {"rxnorm_code": "1649561", "generic_name": "Fluticasone/Salmeterol", "brand_names": ["Advair"], "category": "respiratory", "form": "inhaler", "route": "inhalation", "strength": "250/50mcg", "unit": "mcg", "frequency_options": ["BID"]},
    {"rxnorm_code": "8896", "generic_name": "Prednisone", "brand_names": ["Deltasone"], "category": "antiinflammatory", "form": "tablet", "route": "oral", "strength": "10mg", "unit": "mg", "frequency_options": ["Daily", "BID", "Taper schedule"]},

    # Vitamins/Supplements
    {"rxnorm_code": "11253", "generic_name": "Vitamin D3", "brand_names": [], "category": "vitamin", "form": "tablet", "route": "oral", "strength": "1000 IU", "unit": "IU", "frequency_options": ["Daily"]},
    {"rxnorm_code": "4850", "generic_name": "Ferrous Sulfate", "brand_names": ["Feosol"], "category": "vitamin", "form": "tablet", "route": "oral", "strength": "325mg", "unit": "mg", "frequency_options": ["Daily", "BID", "TID"]},
    {"rxnorm_code": "8337", "generic_name": "Potassium Chloride", "brand_names": ["K-Dur", "Klor-Con"], "category": "vitamin", "form": "tablet", "route": "oral", "strength": "20mEq", "unit": "mEq", "requires_monitoring": True, "monitoring_parameters": "Serum potassium", "frequency_options": ["Daily", "BID"]},
]
