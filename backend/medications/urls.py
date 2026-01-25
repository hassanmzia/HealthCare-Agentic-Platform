from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MedicationCatalogViewSet,
    DrugInteractionViewSet,
    PatientAllergyViewSet,
    PrescriptionViewSet,
    MedicationAdministrationViewSet,
    PatientMedicationHistoryView,
    MedicationStatsView,
)

router = DefaultRouter()
router.register(r"catalog", MedicationCatalogViewSet, basename="medication-catalog")
router.register(r"interactions", DrugInteractionViewSet, basename="drug-interaction")
router.register(r"allergies", PatientAllergyViewSet, basename="patient-allergy")
router.register(r"prescriptions", PrescriptionViewSet, basename="prescription")
router.register(r"administrations", MedicationAdministrationViewSet, basename="medication-administration")

urlpatterns = [
    path("", include(router.urls)),
    path("patient/<int:patient_id>/history/", PatientMedicationHistoryView.as_view(), name="patient-medication-history"),
    path("stats/", MedicationStatsView.as_view(), name="medication-stats"),
]
