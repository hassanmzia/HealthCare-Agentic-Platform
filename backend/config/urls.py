from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/vitals/", include("vitals.urls")),
    path("api/v1/recommendations/", include("recommendations.urls")),
    path("api/v1/patients/", include("patients.urls")),
]

