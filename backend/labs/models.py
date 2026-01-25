"""
Lab models for test ordering, results management, and tracking.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from patients.models import Patient


class LabTestCatalog(models.Model):
    """Catalog of available lab tests with reference ranges."""

    CATEGORY_CHOICES = [
        ("chemistry", "Chemistry"),
        ("hematology", "Hematology"),
        ("urinalysis", "Urinalysis"),
        ("microbiology", "Microbiology"),
        ("immunology", "Immunology"),
        ("coagulation", "Coagulation"),
        ("endocrine", "Endocrine"),
        ("cardiac", "Cardiac Markers"),
        ("toxicology", "Toxicology"),
        ("genetic", "Genetic Testing"),
        ("other", "Other"),
    ]

    SPECIMEN_TYPES = [
        ("blood", "Blood"),
        ("serum", "Serum"),
        ("plasma", "Plasma"),
        ("urine", "Urine"),
        ("stool", "Stool"),
        ("csf", "Cerebrospinal Fluid"),
        ("swab", "Swab"),
        ("tissue", "Tissue"),
        ("other", "Other"),
    ]

    code = models.CharField(max_length=50, unique=True, help_text="LOINC or local code")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    specimen_type = models.CharField(max_length=50, choices=SPECIMEN_TYPES)
    unit = models.CharField(max_length=50, blank=True, help_text="Unit of measurement")

    # Reference ranges (can be overridden per age/gender)
    reference_range_low = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    reference_range_high = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    reference_range_text = models.CharField(max_length=100, blank=True, help_text="Text description of normal range")

    # Critical values
    critical_low = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    critical_high = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)

    # Turnaround time
    typical_tat_hours = models.IntegerField(default=24, help_text="Typical turnaround time in hours")

    # Status
    is_active = models.BooleanField(default=True)
    requires_fasting = models.BooleanField(default=False)
    special_instructions = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lab Test"
        verbose_name_plural = "Lab Test Catalog"
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class LabPanel(models.Model):
    """Pre-defined panels of multiple lab tests."""

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    tests = models.ManyToManyField(LabTestCatalog, related_name="panels")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LabOrder(models.Model):
    """Lab order/requisition for a patient."""

    STATUS_CHOICES = [
        ("ordered", "Ordered"),
        ("collected", "Specimen Collected"),
        ("received", "Received by Lab"),
        ("processing", "Processing"),
        ("partial", "Partial Results"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    PRIORITY_CHOICES = [
        ("routine", "Routine"),
        ("urgent", "Urgent"),
        ("stat", "STAT"),
    ]

    # Order identification
    order_number = models.CharField(max_length=50, unique=True)
    fhir_id = models.CharField(max_length=100, blank=True, help_text="FHIR ServiceRequest ID")

    # Patient and encounter
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="lab_orders")
    encounter_id = models.IntegerField(null=True, blank=True, help_text="Associated encounter ID")

    # Order details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ordered")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="routine")

    # Clinical info
    ordering_physician = models.CharField(max_length=200)
    ordering_physician_id = models.CharField(max_length=100, blank=True)
    clinical_notes = models.TextField(blank=True, help_text="Clinical indication/reason")
    diagnosis_codes = models.JSONField(default=list, blank=True, help_text="ICD-10 codes")

    # Specimen info
    specimen_collected_at = models.DateTimeField(null=True, blank=True)
    specimen_collector = models.CharField(max_length=200, blank=True)
    specimen_id = models.CharField(max_length=100, blank=True)

    # Lab processing
    received_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    ordered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Cancellation
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.CharField(max_length=200, blank=True)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        verbose_name = "Lab Order"
        verbose_name_plural = "Lab Orders"
        ordering = ["-ordered_at"]
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["order_number"]),
            models.Index(fields=["status", "ordered_at"]),
        ]

    def __str__(self):
        return f"{self.order_number} - {self.patient}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            import uuid
            self.order_number = f"LAB-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class LabOrderTest(models.Model):
    """Individual test within a lab order."""

    order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name="tests")
    test = models.ForeignKey(LabTestCatalog, on_delete=models.PROTECT, related_name="order_items")

    # Test-specific status
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Notes
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["order", "test"]
        ordering = ["test__category", "test__name"]

    def __str__(self):
        return f"{self.order.order_number} - {self.test.name}"


class LabResult(models.Model):
    """Result for an individual lab test."""

    FLAG_CHOICES = [
        ("N", "Normal"),
        ("L", "Low"),
        ("H", "High"),
        ("LL", "Critical Low"),
        ("HH", "Critical High"),
        ("A", "Abnormal"),
        ("U", "Undetermined"),
    ]

    # Link to order and test
    order_test = models.OneToOneField(LabOrderTest, on_delete=models.CASCADE, related_name="result")
    fhir_id = models.CharField(max_length=100, blank=True, help_text="FHIR Observation ID")

    # Result value
    value_numeric = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    value_text = models.CharField(max_length=500, blank=True, help_text="Text result or qualitative value")
    unit = models.CharField(max_length=50, blank=True)

    # Reference range (snapshot at time of result)
    reference_range_low = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    reference_range_high = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    reference_range_text = models.CharField(max_length=100, blank=True)

    # Flags and interpretation
    flag = models.CharField(max_length=5, choices=FLAG_CHOICES, default="N")
    is_critical = models.BooleanField(default=False)
    interpretation = models.TextField(blank=True)

    # Performer
    performed_by = models.CharField(max_length=200, blank=True)
    verified_by = models.CharField(max_length=200, blank=True)
    performed_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    # Comments
    comments = models.TextField(blank=True)
    method = models.CharField(max_length=200, blank=True, help_text="Testing method/instrument")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_test.test.name}: {self.value_numeric or self.value_text}"

    def save(self, *args, **kwargs):
        # Auto-calculate flag if numeric value
        if self.value_numeric is not None:
            test = self.order_test.test
            # Check critical values first
            if test.critical_low and self.value_numeric < test.critical_low:
                self.flag = "LL"
                self.is_critical = True
            elif test.critical_high and self.value_numeric > test.critical_high:
                self.flag = "HH"
                self.is_critical = True
            elif self.reference_range_low and self.value_numeric < self.reference_range_low:
                self.flag = "L"
            elif self.reference_range_high and self.value_numeric > self.reference_range_high:
                self.flag = "H"
            else:
                self.flag = "N"

        super().save(*args, **kwargs)


# Common lab tests to seed the catalog
COMMON_LAB_TESTS = [
    # Chemistry
    {"code": "2345-7", "name": "Glucose", "category": "chemistry", "specimen_type": "blood", "unit": "mg/dL", "reference_range_low": 70, "reference_range_high": 100, "critical_low": 40, "critical_high": 500},
    {"code": "2160-0", "name": "Creatinine", "category": "chemistry", "specimen_type": "serum", "unit": "mg/dL", "reference_range_low": 0.7, "reference_range_high": 1.3},
    {"code": "3094-0", "name": "BUN (Blood Urea Nitrogen)", "category": "chemistry", "specimen_type": "serum", "unit": "mg/dL", "reference_range_low": 7, "reference_range_high": 20},
    {"code": "2951-2", "name": "Sodium", "category": "chemistry", "specimen_type": "serum", "unit": "mEq/L", "reference_range_low": 136, "reference_range_high": 145, "critical_low": 120, "critical_high": 160},
    {"code": "2823-3", "name": "Potassium", "category": "chemistry", "specimen_type": "serum", "unit": "mEq/L", "reference_range_low": 3.5, "reference_range_high": 5.0, "critical_low": 2.5, "critical_high": 6.5},
    {"code": "2075-0", "name": "Chloride", "category": "chemistry", "specimen_type": "serum", "unit": "mEq/L", "reference_range_low": 98, "reference_range_high": 106},
    {"code": "2028-9", "name": "CO2 (Bicarbonate)", "category": "chemistry", "specimen_type": "serum", "unit": "mEq/L", "reference_range_low": 22, "reference_range_high": 29},
    {"code": "17861-6", "name": "Calcium", "category": "chemistry", "specimen_type": "serum", "unit": "mg/dL", "reference_range_low": 8.5, "reference_range_high": 10.5, "critical_low": 6.0, "critical_high": 13.0},
    {"code": "1742-6", "name": "ALT (SGPT)", "category": "chemistry", "specimen_type": "serum", "unit": "U/L", "reference_range_low": 7, "reference_range_high": 56},
    {"code": "1920-8", "name": "AST (SGOT)", "category": "chemistry", "specimen_type": "serum", "unit": "U/L", "reference_range_low": 10, "reference_range_high": 40},
    {"code": "1975-2", "name": "Total Bilirubin", "category": "chemistry", "specimen_type": "serum", "unit": "mg/dL", "reference_range_low": 0.1, "reference_range_high": 1.2},
    {"code": "2885-2", "name": "Total Protein", "category": "chemistry", "specimen_type": "serum", "unit": "g/dL", "reference_range_low": 6.0, "reference_range_high": 8.3},
    {"code": "1751-7", "name": "Albumin", "category": "chemistry", "specimen_type": "serum", "unit": "g/dL", "reference_range_low": 3.5, "reference_range_high": 5.0},

    # Hematology
    {"code": "789-8", "name": "RBC (Red Blood Cells)", "category": "hematology", "specimen_type": "blood", "unit": "M/uL", "reference_range_low": 4.5, "reference_range_high": 5.5},
    {"code": "718-7", "name": "Hemoglobin", "category": "hematology", "specimen_type": "blood", "unit": "g/dL", "reference_range_low": 12.0, "reference_range_high": 17.5, "critical_low": 7.0, "critical_high": 20.0},
    {"code": "4544-3", "name": "Hematocrit", "category": "hematology", "specimen_type": "blood", "unit": "%", "reference_range_low": 36, "reference_range_high": 50},
    {"code": "6690-2", "name": "WBC (White Blood Cells)", "category": "hematology", "specimen_type": "blood", "unit": "K/uL", "reference_range_low": 4.5, "reference_range_high": 11.0, "critical_low": 2.0, "critical_high": 30.0},
    {"code": "777-3", "name": "Platelets", "category": "hematology", "specimen_type": "blood", "unit": "K/uL", "reference_range_low": 150, "reference_range_high": 400, "critical_low": 50, "critical_high": 1000},
    {"code": "787-2", "name": "MCV", "category": "hematology", "specimen_type": "blood", "unit": "fL", "reference_range_low": 80, "reference_range_high": 100},
    {"code": "785-6", "name": "MCH", "category": "hematology", "specimen_type": "blood", "unit": "pg", "reference_range_low": 27, "reference_range_high": 33},
    {"code": "786-4", "name": "MCHC", "category": "hematology", "specimen_type": "blood", "unit": "g/dL", "reference_range_low": 32, "reference_range_high": 36},

    # Coagulation
    {"code": "5902-2", "name": "PT (Prothrombin Time)", "category": "coagulation", "specimen_type": "plasma", "unit": "seconds", "reference_range_low": 11, "reference_range_high": 13.5},
    {"code": "6301-6", "name": "INR", "category": "coagulation", "specimen_type": "plasma", "unit": "ratio", "reference_range_low": 0.9, "reference_range_high": 1.1},
    {"code": "3173-2", "name": "PTT (Partial Thromboplastin Time)", "category": "coagulation", "specimen_type": "plasma", "unit": "seconds", "reference_range_low": 25, "reference_range_high": 35},

    # Cardiac
    {"code": "10839-9", "name": "Troponin I", "category": "cardiac", "specimen_type": "serum", "unit": "ng/mL", "reference_range_high": 0.04, "critical_high": 0.5},
    {"code": "33762-6", "name": "BNP", "category": "cardiac", "specimen_type": "blood", "unit": "pg/mL", "reference_range_high": 100},
    {"code": "2093-3", "name": "Total Cholesterol", "category": "cardiac", "specimen_type": "serum", "unit": "mg/dL", "reference_range_high": 200},
    {"code": "2571-8", "name": "Triglycerides", "category": "cardiac", "specimen_type": "serum", "unit": "mg/dL", "reference_range_high": 150},
    {"code": "2085-9", "name": "HDL Cholesterol", "category": "cardiac", "specimen_type": "serum", "unit": "mg/dL", "reference_range_low": 40},
    {"code": "2089-1", "name": "LDL Cholesterol", "category": "cardiac", "specimen_type": "serum", "unit": "mg/dL", "reference_range_high": 100},

    # Endocrine
    {"code": "3016-3", "name": "TSH", "category": "endocrine", "specimen_type": "serum", "unit": "mIU/L", "reference_range_low": 0.4, "reference_range_high": 4.0},
    {"code": "3026-2", "name": "Free T4", "category": "endocrine", "specimen_type": "serum", "unit": "ng/dL", "reference_range_low": 0.8, "reference_range_high": 1.8},
    {"code": "4548-4", "name": "HbA1c", "category": "endocrine", "specimen_type": "blood", "unit": "%", "reference_range_high": 5.7},

    # Urinalysis
    {"code": "5811-5", "name": "Urine Specific Gravity", "category": "urinalysis", "specimen_type": "urine", "unit": "", "reference_range_low": 1.005, "reference_range_high": 1.030},
    {"code": "5803-2", "name": "Urine pH", "category": "urinalysis", "specimen_type": "urine", "unit": "", "reference_range_low": 5.0, "reference_range_high": 8.0},
    {"code": "5804-0", "name": "Urine Protein", "category": "urinalysis", "specimen_type": "urine", "unit": "", "reference_range_text": "Negative"},
    {"code": "5792-7", "name": "Urine Glucose", "category": "urinalysis", "specimen_type": "urine", "unit": "", "reference_range_text": "Negative"},
]

# Common lab panels
COMMON_LAB_PANELS = [
    {"code": "BMP", "name": "Basic Metabolic Panel", "tests": ["2345-7", "2160-0", "3094-0", "2951-2", "2823-3", "2075-0", "2028-9"]},
    {"code": "CMP", "name": "Comprehensive Metabolic Panel", "tests": ["2345-7", "2160-0", "3094-0", "2951-2", "2823-3", "2075-0", "2028-9", "17861-6", "1742-6", "1920-8", "1975-2", "2885-2", "1751-7"]},
    {"code": "CBC", "name": "Complete Blood Count", "tests": ["789-8", "718-7", "4544-3", "6690-2", "777-3", "787-2", "785-6", "786-4"]},
    {"code": "LIPID", "name": "Lipid Panel", "tests": ["2093-3", "2571-8", "2085-9", "2089-1"]},
    {"code": "LFT", "name": "Liver Function Tests", "tests": ["1742-6", "1920-8", "1975-2", "2885-2", "1751-7"]},
    {"code": "COAG", "name": "Coagulation Panel", "tests": ["5902-2", "6301-6", "3173-2"]},
    {"code": "THYROID", "name": "Thyroid Panel", "tests": ["3016-3", "3026-2"]},
]
