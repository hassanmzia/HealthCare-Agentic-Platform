from django.urls import path
from .views import (
    PatientListView,
    PatientDetailView,
    PatientImportView,
    PatientDocumentListView,
    PatientByMRNView,
    PatientByFHIRView,
    PatientResyncView,
)

urlpatterns = [
    # Patient CRUD
    path("", PatientListView.as_view(), name="patient-list"),
    path("<int:patient_id>/", PatientDetailView.as_view(), name="patient-detail"),

    # Import
    path("import/", PatientImportView.as_view(), name="patient-import"),

    # FHIR sync
    path("<int:patient_id>/resync/", PatientResyncView.as_view(), name="patient-resync"),

    # Documents
    path("<int:patient_id>/documents/", PatientDocumentListView.as_view(), name="patient-documents"),

    # Lookup by identifiers
    path("by-mrn/<str:mrn>/", PatientByMRNView.as_view(), name="patient-by-mrn"),
    path("by-fhir/<str:fhir_id>/", PatientByFHIRView.as_view(), name="patient-by-fhir"),
]
