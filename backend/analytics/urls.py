from django.urls import path
from .views import (
    OverviewStatsView,
    VitalsAnalyticsView,
    AlertAnalyticsView,
    DeviceAnalyticsView,
    PatientAnalyticsView,
    ClinicalAnalyticsView,
)

urlpatterns = [
    path("overview/", OverviewStatsView.as_view(), name="analytics-overview"),
    path("vitals/", VitalsAnalyticsView.as_view(), name="analytics-vitals"),
    path("alerts/", AlertAnalyticsView.as_view(), name="analytics-alerts"),
    path("devices/", DeviceAnalyticsView.as_view(), name="analytics-devices"),
    path("patients/", PatientAnalyticsView.as_view(), name="analytics-patients"),
    path("clinical/", ClinicalAnalyticsView.as_view(), name="analytics-clinical"),
]
