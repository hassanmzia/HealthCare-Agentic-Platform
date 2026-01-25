from django.urls import path
from .views import (
    AlertListView, AlertDetailView,
    AcknowledgeAlertView, ResolveAlertView, BulkAcknowledgeView,
    AlertSummaryView,
    AlertRuleListView, AlertRuleDetailView, InitializeDefaultRulesView,
    PatientAlertsView,
    CheckVitalsView,
)

urlpatterns = [
    # Alerts
    path("", AlertListView.as_view(), name="alert-list"),
    path("<int:alert_id>/", AlertDetailView.as_view(), name="alert-detail"),
    path("<int:alert_id>/acknowledge/", AcknowledgeAlertView.as_view(), name="alert-acknowledge"),
    path("<int:alert_id>/resolve/", ResolveAlertView.as_view(), name="alert-resolve"),
    path("bulk-acknowledge/", BulkAcknowledgeView.as_view(), name="alert-bulk-acknowledge"),
    path("summary/", AlertSummaryView.as_view(), name="alert-summary"),

    # Alert Rules
    path("rules/", AlertRuleListView.as_view(), name="alert-rule-list"),
    path("rules/<int:rule_id>/", AlertRuleDetailView.as_view(), name="alert-rule-detail"),
    path("rules/initialize-defaults/", InitializeDefaultRulesView.as_view(), name="alert-rule-init"),

    # Patient-specific
    path("patient/<int:patient_id>/", PatientAlertsView.as_view(), name="patient-alerts"),

    # Vital checking endpoint (for IoT simulator)
    path("check-vitals/", CheckVitalsView.as_view(), name="check-vitals"),
]
