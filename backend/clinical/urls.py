from django.urls import path
from .views import (
    EncounterListView, EncounterDetailView,
    ClinicalNoteListView, ClinicalNoteDetailView, SignNoteView,
    DiagnosisListView, DiagnosisDetailView,
    CarePlanListView, CarePlanDetailView,
    VitalsListView, VitalsDetailView,
    PatientClinicalSummaryView,
    # AI Assessment Views
    ClinicalAssessmentListView, ClinicalAssessmentDetailView,
    # Physician Review Views
    PhysicianReviewListView, PhysicianReviewSubmitView, PhysicianReviewDetailView,
    # Audit Log Views
    AssessmentAuditLogView,
    # Document Generation Views
    ClinicalDocumentListView, GenerateDocumentView, ClinicalDocumentDetailView,
    ClinicalDocumentDownloadView,
    # EHR Order Views
    EHROrderListView, CreateEHROrdersView, EHROrderDetailView,
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

    # ==========================================================================
    # AI Clinical Assessment Endpoints
    # ==========================================================================

    # Assessments
    path("assessments/", ClinicalAssessmentListView.as_view(), name="assessment-list"),
    path("assessments/<uuid:assessment_id>/", ClinicalAssessmentDetailView.as_view(), name="assessment-detail"),
    path("assessments/<uuid:assessment_id>/audit/", AssessmentAuditLogView.as_view(), name="assessment-audit"),

    # Physician Reviews
    path("reviews/", PhysicianReviewListView.as_view(), name="review-list"),
    path("reviews/submit/", PhysicianReviewSubmitView.as_view(), name="review-submit"),
    path("reviews/<uuid:review_id>/", PhysicianReviewDetailView.as_view(), name="review-detail"),

    # Clinical Documents
    path("documents/", ClinicalDocumentListView.as_view(), name="document-list"),
    path("documents/generate/", GenerateDocumentView.as_view(), name="document-generate"),
    path("documents/<uuid:document_id>/", ClinicalDocumentDetailView.as_view(), name="document-detail"),
    path("documents/<uuid:document_id>/download/", ClinicalDocumentDownloadView.as_view(), name="document-download"),

    # EHR Orders
    path("orders/", EHROrderListView.as_view(), name="order-list"),
    path("orders/create/", CreateEHROrdersView.as_view(), name="order-create"),
    path("orders/<uuid:order_id>/", EHROrderDetailView.as_view(), name="order-detail"),
]
