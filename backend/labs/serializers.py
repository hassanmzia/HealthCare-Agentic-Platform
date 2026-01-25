"""
Lab serializers for orders, tests, and results.
"""

from rest_framework import serializers
from .models import LabTestCatalog, LabPanel, LabOrder, LabOrderTest, LabResult


class LabTestCatalogSerializer(serializers.ModelSerializer):
    """Serializer for lab test catalog."""

    class Meta:
        model = LabTestCatalog
        fields = [
            "id", "code", "name", "description", "category", "specimen_type", "unit",
            "reference_range_low", "reference_range_high", "reference_range_text",
            "critical_low", "critical_high", "typical_tat_hours", "is_active",
            "requires_fasting", "special_instructions", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LabPanelSerializer(serializers.ModelSerializer):
    """Serializer for lab panels."""

    tests = LabTestCatalogSerializer(many=True, read_only=True)
    test_codes = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = LabPanel
        fields = ["id", "code", "name", "description", "tests", "test_codes", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        test_codes = validated_data.pop("test_codes", [])
        panel = LabPanel.objects.create(**validated_data)
        if test_codes:
            tests = LabTestCatalog.objects.filter(code__in=test_codes)
            panel.tests.set(tests)
        return panel

    def update(self, instance, validated_data):
        test_codes = validated_data.pop("test_codes", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if test_codes is not None:
            tests = LabTestCatalog.objects.filter(code__in=test_codes)
            instance.tests.set(tests)
        return instance


class LabResultSerializer(serializers.ModelSerializer):
    """Serializer for lab results."""

    test_name = serializers.CharField(source="order_test.test.name", read_only=True)
    test_code = serializers.CharField(source="order_test.test.code", read_only=True)
    test_unit = serializers.CharField(source="order_test.test.unit", read_only=True)

    class Meta:
        model = LabResult
        fields = [
            "id", "order_test", "fhir_id", "test_name", "test_code", "test_unit",
            "value_numeric", "value_text", "unit",
            "reference_range_low", "reference_range_high", "reference_range_text",
            "flag", "is_critical", "interpretation",
            "performed_by", "verified_by", "performed_at", "verified_at",
            "comments", "method", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "flag", "is_critical", "created_at", "updated_at"]


class LabOrderTestSerializer(serializers.ModelSerializer):
    """Serializer for tests within an order."""

    test_details = LabTestCatalogSerializer(source="test", read_only=True)
    result = LabResultSerializer(read_only=True)
    test_id = serializers.IntegerField(write_only=True, required=False)
    test_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = LabOrderTest
        fields = ["id", "order", "test", "test_id", "test_code", "test_details", "status", "notes", "result", "created_at"]
        read_only_fields = ["id", "order", "test", "created_at"]


class LabOrderSerializer(serializers.ModelSerializer):
    """Serializer for lab orders."""

    patient_name = serializers.SerializerMethodField()
    patient_mrn = serializers.CharField(source="patient.mrn", read_only=True)
    tests = LabOrderTestSerializer(many=True, read_only=True)
    test_codes = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    panel_codes = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = LabOrder
        fields = [
            "id", "order_number", "fhir_id", "patient", "patient_name", "patient_mrn",
            "encounter_id", "status", "priority",
            "ordering_physician", "ordering_physician_id", "clinical_notes", "diagnosis_codes",
            "specimen_collected_at", "specimen_collector", "specimen_id",
            "received_at", "completed_at", "ordered_at", "updated_at",
            "cancelled_at", "cancelled_by", "cancellation_reason",
            "tests", "test_codes", "panel_codes"
        ]
        read_only_fields = [
            "id", "order_number", "ordered_at", "updated_at",
            "cancelled_at", "cancelled_by"
        ]

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    def create(self, validated_data):
        test_codes = validated_data.pop("test_codes", [])
        panel_codes = validated_data.pop("panel_codes", [])

        order = LabOrder.objects.create(**validated_data)

        # Add tests from test codes
        all_test_codes = set(test_codes)

        # Add tests from panels
        if panel_codes:
            panels = LabPanel.objects.filter(code__in=panel_codes, is_active=True)
            for panel in panels:
                for test in panel.tests.all():
                    all_test_codes.add(test.code)

        # Create order tests
        tests = LabTestCatalog.objects.filter(code__in=all_test_codes, is_active=True)
        for test in tests:
            LabOrderTest.objects.create(order=order, test=test)

        return order


class LabOrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for lab order lists."""

    patient_name = serializers.SerializerMethodField()
    patient_mrn = serializers.CharField(source="patient.mrn", read_only=True)
    test_count = serializers.SerializerMethodField()
    completed_count = serializers.SerializerMethodField()

    class Meta:
        model = LabOrder
        fields = [
            "id", "order_number", "patient", "patient_name", "patient_mrn",
            "status", "priority", "ordering_physician",
            "test_count", "completed_count",
            "ordered_at", "completed_at"
        ]

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    def get_test_count(self, obj):
        return obj.tests.count()

    def get_completed_count(self, obj):
        return obj.tests.filter(status="completed").count()


class LabOrderStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating order status."""

    status = serializers.ChoiceField(choices=LabOrder.STATUS_CHOICES)
    specimen_collected_at = serializers.DateTimeField(required=False)
    specimen_collector = serializers.CharField(required=False, allow_blank=True)
    specimen_id = serializers.CharField(required=False, allow_blank=True)
    received_at = serializers.DateTimeField(required=False)
    completed_at = serializers.DateTimeField(required=False)


class LabOrderCancelSerializer(serializers.Serializer):
    """Serializer for cancelling an order."""

    reason = serializers.CharField(required=True)
    cancelled_by = serializers.CharField(required=True)


class ResultEntrySerializer(serializers.Serializer):
    """Serializer for batch result entry."""

    order_test_id = serializers.IntegerField()
    value_numeric = serializers.DecimalField(max_digits=15, decimal_places=5, required=False, allow_null=True)
    value_text = serializers.CharField(required=False, allow_blank=True)
    performed_by = serializers.CharField(required=False, allow_blank=True)
    comments = serializers.CharField(required=False, allow_blank=True)
    method = serializers.CharField(required=False, allow_blank=True)


class PatientLabHistorySerializer(serializers.Serializer):
    """Serializer for patient lab history with trends."""

    test_code = serializers.CharField()
    test_name = serializers.CharField()
    unit = serializers.CharField()
    reference_range_low = serializers.DecimalField(max_digits=10, decimal_places=3, allow_null=True)
    reference_range_high = serializers.DecimalField(max_digits=10, decimal_places=3, allow_null=True)
    results = serializers.ListField(child=serializers.DictField())
