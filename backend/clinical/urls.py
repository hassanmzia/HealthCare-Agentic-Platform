from django.urls import path
from .views import (
    EncounterListView, EncounterDetailView,
    ClinicalNoteListView, ClinicalNoteDetailView, SignNoteView,
    DiagnosisListView, DiagnosisDetailView,
    CarePlanListView, CarePlanDetailView,
    VitalsListView, VitalsDetailView,
    PatientClinicalSummaryView,
)

urlpatterns = [
    # Encounters
    path("encounters/", EncounterListView.as_view(), name="encounter-list"),
    path("encounters/<int:encounter_id>/", EncounterDetailView.as_view(), name="encounter-detail"),

    # Clinical Notes
    path("notes/", ClinicalNoteListView.as_view(), name="note-list"),
    path("notes/<int:note_id>/", ClinicalNoteDetailView.as_view(), name="note-detail"),
    path("notes/<int:note_id>/sign/", SignNoteView.as_view(), name="note-sign"),

    # Diagnoses
    path("diagnoses/", DiagnosisListView.as_view(), name="diagnosis-list"),
    path("diagnoses/<int:diagnosis_id>/", DiagnosisDetailView.as_view(), name="diagnosis-detail"),

    # Care Plans
    path("careplans/", CarePlanListView.as_view(), name="careplan-list"),
    path("careplans/<int:plan_id>/", CarePlanDetailView.as_view(), name="careplan-detail"),

    # Vitals
    path("vitals/", VitalsListView.as_view(), name="vitals-list"),
    path("vitals/<int:vitals_id>/", VitalsDetailView.as_view(), name="vitals-detail"),

    # Patient Summary
    path("patient/<int:patient_id>/summary/", PatientClinicalSummaryView.as_view(), name="patient-summary"),
]
