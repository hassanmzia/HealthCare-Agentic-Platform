"""
Lab views for orders, tests, results, and catalog management.
"""

from collections import defaultdict
from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import (
    LabTestCatalog, LabPanel, LabOrder, LabOrderTest, LabResult,
    COMMON_LAB_TESTS, COMMON_LAB_PANELS
)
from .serializers import (
    LabTestCatalogSerializer,
    LabPanelSerializer,
    LabOrderSerializer,
    LabOrderListSerializer,
    LabOrderTestSerializer,
    LabResultSerializer,
    LabOrderStatusUpdateSerializer,
    LabOrderCancelSerializer,
    ResultEntrySerializer,
)


# ============ Lab Test Catalog Views ============

class LabTestCatalogListView(APIView):
    """List and create lab tests in catalog."""

    def get(self, request):
        tests = LabTestCatalog.objects.all()

        # Filtering
        category = request.query_params.get("category")
        if category:
            tests = tests.filter(category=category)

        search = request.query_params.get("search")
        if search:
            tests = tests.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )

        active_only = request.query_params.get("active_only", "true").lower() == "true"
        if active_only:
            tests = tests.filter(is_active=True)

        # Pagination
        limit = int(request.query_params.get("limit", 100))
        offset = int(request.query_params.get("offset", 0))
        total = tests.count()
        tests = tests[offset:offset + limit]

        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": LabTestCatalogSerializer(tests, many=True).data
        })

    def post(self, request):
        serializer = LabTestCatalogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LabTestCatalogDetailView(APIView):
    """Get, update, delete a lab test from catalog."""

    def get_test(self, test_id):
        try:
            return LabTestCatalog.objects.get(id=test_id)
        except LabTestCatalog.DoesNotExist:
            return None

    def get(self, request, test_id):
        test = self.get_test(test_id)
        if not test:
            return Response({"error": "Test not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(LabTestCatalogSerializer(test).data)

    def put(self, request, test_id):
        test = self.get_test(test_id)
        if not test:
            return Response({"error": "Test not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = LabTestCatalogSerializer(test, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, test_id):
        test = self.get_test(test_id)
        if not test:
            return Response({"error": "Test not found"}, status=status.HTTP_404_NOT_FOUND)

        # Soft delete - just deactivate
        test.is_active = False
        test.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InitializeLabCatalogView(APIView):
    """Initialize lab catalog with common tests."""

    def post(self, request):
        created_tests = 0
        created_panels = 0

        # Create tests
        for test_data in COMMON_LAB_TESTS:
            test, created = LabTestCatalog.objects.get_or_create(
                code=test_data["code"],
                defaults=test_data
            )
            if created:
                created_tests += 1

        # Create panels
        for panel_data in COMMON_LAB_PANELS:
            test_codes = panel_data.pop("tests")
            panel, created = LabPanel.objects.get_or_create(
                code=panel_data["code"],
                defaults=panel_data
            )
            if created:
                created_panels += 1
                tests = LabTestCatalog.objects.filter(code__in=test_codes)
                panel.tests.set(tests)

        return Response({
            "message": "Lab catalog initialized",
            "tests_created": created_tests,
            "panels_created": created_panels,
            "total_tests": LabTestCatalog.objects.count(),
            "total_panels": LabPanel.objects.count(),
        })


# ============ Lab Panel Views ============

class LabPanelListView(APIView):
    """List and create lab panels."""

    def get(self, request):
        panels = LabPanel.objects.filter(is_active=True).prefetch_related("tests")
        return Response({
            "total": panels.count(),
            "results": LabPanelSerializer(panels, many=True).data
        })

    def post(self, request):
        serializer = LabPanelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============ Lab Order Views ============

class LabOrderListView(APIView):
    """List and create lab orders."""

    def get(self, request):
        orders = LabOrder.objects.all().select_related("patient")

        # Filtering
        patient_id = request.query_params.get("patient_id")
        if patient_id:
            orders = orders.filter(patient_id=patient_id)

        status_filter = request.query_params.get("status")
        if status_filter:
            orders = orders.filter(status=status_filter)

        priority = request.query_params.get("priority")
        if priority:
            orders = orders.filter(priority=priority)

        physician = request.query_params.get("physician")
        if physician:
            orders = orders.filter(ordering_physician__icontains=physician)

        # Date range
        start_date = request.query_params.get("start_date")
        if start_date:
            orders = orders.filter(ordered_at__date__gte=start_date)

        end_date = request.query_params.get("end_date")
        if end_date:
            orders = orders.filter(ordered_at__date__lte=end_date)

        # Pagination
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))
        total = orders.count()
        orders = orders[offset:offset + limit]

        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": LabOrderListSerializer(orders, many=True).data
        })

    def post(self, request):
        serializer = LabOrderSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save()
            return Response(LabOrderSerializer(order).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LabOrderDetailView(APIView):
    """Get, update a lab order."""

    def get_order(self, order_id):
        try:
            return LabOrder.objects.select_related("patient").prefetch_related(
                "tests__test", "tests__result"
            ).get(id=order_id)
        except LabOrder.DoesNotExist:
            return None

    def get(self, request, order_id):
        order = self.get_order(order_id)
        if not order:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(LabOrderSerializer(order).data)

    def put(self, request, order_id):
        order = self.get_order(order_id)
        if not order:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.status == "cancelled":
            return Response({"error": "Cannot modify cancelled order"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LabOrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(LabOrderSerializer(order).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LabOrderStatusView(APIView):
    """Update lab order status."""

    def post(self, request, order_id):
        try:
            order = LabOrder.objects.get(id=order_id)
        except LabOrder.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.status == "cancelled":
            return Response({"error": "Cannot modify cancelled order"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LabOrderStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            order.status = data["status"]

            if data.get("specimen_collected_at"):
                order.specimen_collected_at = data["specimen_collected_at"]
            if data.get("specimen_collector"):
                order.specimen_collector = data["specimen_collector"]
            if data.get("specimen_id"):
                order.specimen_id = data["specimen_id"]
            if data.get("received_at"):
                order.received_at = data["received_at"]
            if data.get("completed_at"):
                order.completed_at = data["completed_at"]

            order.save()
            return Response(LabOrderSerializer(order).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LabOrderCancelView(APIView):
    """Cancel a lab order."""

    def post(self, request, order_id):
        try:
            order = LabOrder.objects.get(id=order_id)
        except LabOrder.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.status == "cancelled":
            return Response({"error": "Order already cancelled"}, status=status.HTTP_400_BAD_REQUEST)

        if order.status == "completed":
            return Response({"error": "Cannot cancel completed order"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LabOrderCancelSerializer(data=request.data)
        if serializer.is_valid():
            order.status = "cancelled"
            order.cancelled_at = timezone.now()
            order.cancelled_by = serializer.validated_data["cancelled_by"]
            order.cancellation_reason = serializer.validated_data["reason"]
            order.save()

            # Cancel all pending tests
            order.tests.filter(status="pending").update(status="cancelled")

            return Response(LabOrderSerializer(order).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LabOrderAddTestView(APIView):
    """Add tests to an existing order."""

    def post(self, request, order_id):
        try:
            order = LabOrder.objects.get(id=order_id)
        except LabOrder.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.status in ["cancelled", "completed"]:
            return Response({"error": "Cannot add tests to cancelled/completed order"}, status=status.HTTP_400_BAD_REQUEST)

        test_codes = request.data.get("test_codes", [])
        panel_codes = request.data.get("panel_codes", [])

        all_test_codes = set(test_codes)

        # Add tests from panels
        if panel_codes:
            panels = LabPanel.objects.filter(code__in=panel_codes, is_active=True)
            for panel in panels:
                for test in panel.tests.all():
                    all_test_codes.add(test.code)

        # Create order tests (skip existing)
        existing_codes = set(order.tests.values_list("test__code", flat=True))
        new_codes = all_test_codes - existing_codes

        tests = LabTestCatalog.objects.filter(code__in=new_codes, is_active=True)
        added = []
        for test in tests:
            order_test = LabOrderTest.objects.create(order=order, test=test)
            added.append(test.code)

        return Response({
            "added_tests": added,
            "order": LabOrderSerializer(order).data
        })


# ============ Lab Result Views ============

class LabResultEntryView(APIView):
    """Enter results for lab tests."""

    def post(self, request, order_id):
        try:
            order = LabOrder.objects.get(id=order_id)
        except LabOrder.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.status == "cancelled":
            return Response({"error": "Cannot enter results for cancelled order"}, status=status.HTTP_400_BAD_REQUEST)

        results_data = request.data.get("results", [])
        entered = []
        errors = []

        for result_item in results_data:
            serializer = ResultEntrySerializer(data=result_item)
            if serializer.is_valid():
                data = serializer.validated_data
                try:
                    order_test = LabOrderTest.objects.get(
                        id=data["order_test_id"],
                        order=order
                    )

                    # Get reference ranges from catalog
                    test = order_test.test

                    result, created = LabResult.objects.update_or_create(
                        order_test=order_test,
                        defaults={
                            "value_numeric": data.get("value_numeric"),
                            "value_text": data.get("value_text", ""),
                            "unit": test.unit,
                            "reference_range_low": test.reference_range_low,
                            "reference_range_high": test.reference_range_high,
                            "reference_range_text": test.reference_range_text,
                            "performed_by": data.get("performed_by", ""),
                            "performed_at": timezone.now(),
                            "comments": data.get("comments", ""),
                            "method": data.get("method", ""),
                        }
                    )

                    # Update order test status
                    order_test.status = "completed"
                    order_test.save()

                    entered.append({
                        "order_test_id": order_test.id,
                        "test_name": test.name,
                        "flag": result.flag,
                        "is_critical": result.is_critical,
                    })

                except LabOrderTest.DoesNotExist:
                    errors.append({"order_test_id": data["order_test_id"], "error": "Test not found in order"})
            else:
                errors.append(serializer.errors)

        # Update order status
        total_tests = order.tests.count()
        completed_tests = order.tests.filter(status="completed").count()

        if completed_tests == total_tests:
            order.status = "completed"
            order.completed_at = timezone.now()
        elif completed_tests > 0:
            order.status = "partial"
        order.save()

        # Check for critical values
        critical_results = [r for r in entered if r.get("is_critical")]

        return Response({
            "entered": entered,
            "errors": errors,
            "order_status": order.status,
            "critical_results": critical_results,
        })


class LabResultDetailView(APIView):
    """Get or update a specific result."""

    def get(self, request, result_id):
        try:
            result = LabResult.objects.select_related("order_test__test", "order_test__order").get(id=result_id)
        except LabResult.DoesNotExist:
            return Response({"error": "Result not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(LabResultSerializer(result).data)

    def put(self, request, result_id):
        try:
            result = LabResult.objects.get(id=result_id)
        except LabResult.DoesNotExist:
            return Response({"error": "Result not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = LabResultSerializer(result, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyResultView(APIView):
    """Verify/sign off on a result."""

    def post(self, request, result_id):
        try:
            result = LabResult.objects.get(id=result_id)
        except LabResult.DoesNotExist:
            return Response({"error": "Result not found"}, status=status.HTTP_404_NOT_FOUND)

        verified_by = request.data.get("verified_by")
        if not verified_by:
            return Response({"error": "verified_by is required"}, status=status.HTTP_400_BAD_REQUEST)

        result.verified_by = verified_by
        result.verified_at = timezone.now()
        result.save()

        return Response(LabResultSerializer(result).data)


# ============ Patient Lab History ============

class PatientLabHistoryView(APIView):
    """Get lab history for a patient with trends."""

    def get(self, request, patient_id):
        test_code = request.query_params.get("test_code")
        days = int(request.query_params.get("days", 365))

        # Get all results for patient
        results = LabResult.objects.filter(
            order_test__order__patient_id=patient_id,
            order_test__status="completed"
        ).select_related(
            "order_test__test", "order_test__order"
        ).order_by("-performed_at")

        if test_code:
            results = results.filter(order_test__test__code=test_code)

        # Group by test
        test_history = defaultdict(list)
        for result in results:
            test = result.order_test.test
            test_history[test.code].append({
                "result_id": result.id,
                "order_number": result.order_test.order.order_number,
                "value_numeric": float(result.value_numeric) if result.value_numeric else None,
                "value_text": result.value_text,
                "unit": result.unit,
                "flag": result.flag,
                "is_critical": result.is_critical,
                "performed_at": result.performed_at.isoformat() if result.performed_at else None,
                "reference_range_low": float(result.reference_range_low) if result.reference_range_low else None,
                "reference_range_high": float(result.reference_range_high) if result.reference_range_high else None,
            })

        # Format response
        history = []
        for code, results_list in test_history.items():
            test = LabTestCatalog.objects.filter(code=code).first()
            if test:
                history.append({
                    "test_code": code,
                    "test_name": test.name,
                    "unit": test.unit,
                    "category": test.category,
                    "reference_range_low": float(test.reference_range_low) if test.reference_range_low else None,
                    "reference_range_high": float(test.reference_range_high) if test.reference_range_high else None,
                    "results": results_list[:50],  # Limit to last 50
                })

        return Response({
            "patient_id": patient_id,
            "tests": history,
        })


# ============ Lab Statistics ============

class LabStatsView(APIView):
    """Get lab order and result statistics."""

    def get(self, request):
        now = timezone.now()
        today = now.date()

        # Order counts by status
        status_counts = dict(
            LabOrder.objects.values("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )

        # Orders today
        orders_today = LabOrder.objects.filter(ordered_at__date=today).count()

        # Pending orders
        pending_orders = LabOrder.objects.filter(
            status__in=["ordered", "collected", "received", "processing"]
        ).count()

        # Critical results today
        critical_today = LabResult.objects.filter(
            is_critical=True,
            created_at__date=today
        ).count()

        # Average TAT (completed orders from last 7 days)
        from django.db.models import F, Avg
        from datetime import timedelta

        completed_orders = LabOrder.objects.filter(
            status="completed",
            completed_at__isnull=False,
            ordered_at__gte=now - timedelta(days=7)
        ).annotate(
            tat_seconds=F("completed_at") - F("ordered_at")
        )

        avg_tat_hours = None
        if completed_orders.exists():
            total_seconds = sum(
                (o.completed_at - o.ordered_at).total_seconds()
                for o in completed_orders
            )
            avg_tat_hours = round(total_seconds / completed_orders.count() / 3600, 1)

        # Top ordered tests
        top_tests = list(
            LabOrderTest.objects.values("test__name", "test__code")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        return Response({
            "orders_by_status": status_counts,
            "orders_today": orders_today,
            "pending_orders": pending_orders,
            "critical_results_today": critical_today,
            "average_tat_hours": avg_tat_hours,
            "top_ordered_tests": top_tests,
            "total_tests_in_catalog": LabTestCatalog.objects.filter(is_active=True).count(),
            "total_panels": LabPanel.objects.filter(is_active=True).count(),
        })
