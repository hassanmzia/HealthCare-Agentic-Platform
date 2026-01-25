from django.urls import path
from .views import (
    DeviceListView,
    DeviceDetailView,
    DeviceAssignView,
    DeviceUnassignView,
    DeviceByDeviceIdView,
    PatientDevicesView,
    DeviceAssignmentHistoryView,
)

urlpatterns = [
    # Device CRUD
    path("", DeviceListView.as_view(), name="device-list"),
    path("<int:device_id>/", DeviceDetailView.as_view(), name="device-detail"),

    # Assignment
    path("<int:device_id>/assign/", DeviceAssignView.as_view(), name="device-assign"),
    path("<int:device_id>/unassign/", DeviceUnassignView.as_view(), name="device-unassign"),
    path("<int:device_id>/assignments/", DeviceAssignmentHistoryView.as_view(), name="device-assignments"),

    # Lookup
    path("by-device-id/<str:device_id>/", DeviceByDeviceIdView.as_view(), name="device-by-device-id"),

    # Patient's devices
    path("patient/<int:patient_id>/", PatientDevicesView.as_view(), name="patient-devices"),
]
