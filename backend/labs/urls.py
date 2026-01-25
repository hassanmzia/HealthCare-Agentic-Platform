from django.urls import path
from .views import (
    LabTestCatalogListView,
    LabTestCatalogDetailView,
    InitializeLabCatalogView,
    LabPanelListView,
    LabOrderListView,
    LabOrderDetailView,
    LabOrderStatusView,
    LabOrderCancelView,
    LabOrderAddTestView,
    LabResultEntryView,
    LabResultDetailView,
    VerifyResultView,
    PatientLabHistoryView,
    LabStatsView,
)

urlpatterns = [
    # Lab Test Catalog
    path("catalog/", LabTestCatalogListView.as_view(), name="lab-catalog-list"),
    path("catalog/<int:test_id>/", LabTestCatalogDetailView.as_view(), name="lab-catalog-detail"),
    path("catalog/initialize/", InitializeLabCatalogView.as_view(), name="lab-catalog-initialize"),

    # Lab Panels
    path("panels/", LabPanelListView.as_view(), name="lab-panel-list"),

    # Lab Orders
    path("orders/", LabOrderListView.as_view(), name="lab-order-list"),
    path("orders/<int:order_id>/", LabOrderDetailView.as_view(), name="lab-order-detail"),
    path("orders/<int:order_id>/status/", LabOrderStatusView.as_view(), name="lab-order-status"),
    path("orders/<int:order_id>/cancel/", LabOrderCancelView.as_view(), name="lab-order-cancel"),
    path("orders/<int:order_id>/add-tests/", LabOrderAddTestView.as_view(), name="lab-order-add-tests"),
    path("orders/<int:order_id>/results/", LabResultEntryView.as_view(), name="lab-result-entry"),

    # Results
    path("results/<int:result_id>/", LabResultDetailView.as_view(), name="lab-result-detail"),
    path("results/<int:result_id>/verify/", VerifyResultView.as_view(), name="lab-result-verify"),

    # Patient History
    path("patient/<int:patient_id>/history/", PatientLabHistoryView.as_view(), name="patient-lab-history"),

    # Statistics
    path("stats/", LabStatsView.as_view(), name="lab-stats"),
]
