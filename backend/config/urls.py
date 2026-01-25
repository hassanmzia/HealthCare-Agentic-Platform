from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/vitals/", include("vitals.urls")),
    path("api/v1/recommendations/", include("recommendations.urls")),
    path("api/v1/patients/", include("patients.urls")),
    path("api/v1/devices/", include("devices.urls")),
    path("api/v1/clinical/", include("clinical.urls")),
    path("api/v1/alerts/", include("alerts.urls")),
    path("api/v1/analytics/", include("analytics.urls")),
    path("api/v1/users/", include("users.urls")),
    path("api/v1/labs/", include("labs.urls")),
]

