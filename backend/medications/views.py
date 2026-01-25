import uuid
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    MedicationCatalog,
    DrugInteraction,
    PatientAllergy,
    Prescription,
    MedicationAdministration,
    COMMON_MEDICATIONS,
)
from .serializers import (
    MedicationCatalogSerializer,
    MedicationCatalogListSerializer,
    DrugInteractionSerializer,
    PatientAllergySerializer,
    PrescriptionSerializer,
    PrescriptionListSerializer,
    PrescriptionCreateSerializer,
    MedicationAdministrationSerializer,
    MedicationAdministrationListSerializer,
)


class MedicationCatalogViewSet(viewsets.ModelViewSet):
    """ViewSet for medication catalog management."""

    queryset = MedicationCatalog.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return MedicationCatalogListSerializer
        return MedicationCatalogSerializer

    def get_queryset(self):
        queryset = MedicationCatalog.objects.all()

        # Filter by active status
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        # Filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        # Filter by form
        form = self.request.query_params.get("form")
        if form:
            queryset = queryset.filter(form=form)

        # Filter by route
        route = self.request.query_params.get("route")
        if route:
            queryset = queryset.filter(route=route)

        # Filter controlled substances
        is_controlled = self.request.query_params.get("is_controlled")
        if is_controlled is not None:
            queryset = queryset.filter(is_controlled=is_controlled.lower() == "true")

        # Filter high-alert medications
        is_high_alert = self.request.query_params.get("is_high_alert")
        if is_high_alert is not None:
            queryset = queryset.filter(is_high_alert=is_high_alert.lower() == "true")

        # Search by name
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(generic_name__icontains=search) |
                Q(brand_names__icontains=search) |
                Q(rxnorm_code__icontains=search)
            )

        return queryset.order_by("generic_name")

    @action(detail=False, methods=["post"])
    def seed(self, request):
        """Seed the medication catalog with common medications."""
        created_count = 0
        updated_count = 0

        for med_data in COMMON_MEDICATIONS:
            rxnorm_code = med_data["rxnorm_code"]
            defaults = {k: v for k, v in med_data.items() if k != "rxnorm_code"}

            obj, created = MedicationCatalog.objects.update_or_create(
                rxnorm_code=rxnorm_code,
                defaults=defaults
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        return Response({
            "message": f"Seeded medication catalog: {created_count} created, {updated_count} updated",
            "total": len(COMMON_MEDICATIONS)
        })


class DrugInteractionViewSet(viewsets.ModelViewSet):
    """ViewSet for drug interactions."""

    queryset = DrugInteraction.objects.all()
    serializer_class = DrugInteractionSerializer

    def get_queryset(self):
        queryset = DrugInteraction.objects.all()

        # Filter by drug
        drug_id = self.request.query_params.get("drug_id")
        if drug_id:
            queryset = queryset.filter(
                Q(drug_a_id=drug_id) | Q(drug_b_id=drug_id)
            )

        # Filter by severity
        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)

        return queryset

    @action(detail=False, methods=["post"])
    def check(self, request):
        """Check for interactions between a list of medications."""
        medication_ids = request.data.get("medication_ids", [])

        if len(medication_ids) < 2:
            return Response({
                "interactions": [],
                "message": "Need at least 2 medications to check for interactions"
            })

        interactions = DrugInteraction.objects.filter(
            Q(drug_a_id__in=medication_ids, drug_b_id__in=medication_ids)
        )

        serializer = DrugInteractionSerializer(interactions, many=True)
        return Response({
            "interactions": serializer.data,
            "has_major": interactions.filter(severity__in=["major", "contraindicated"]).exists(),
            "count": interactions.count()
        })


class PatientAllergyViewSet(viewsets.ModelViewSet):
    """ViewSet for patient allergies."""

    queryset = PatientAllergy.objects.all()
    serializer_class = PatientAllergySerializer

    def get_queryset(self):
        queryset = PatientAllergy.objects.all()

        # Filter by patient
        patient_id = self.request.query_params.get("patient_id")
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        # Filter by active status
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        # Filter by severity
        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)

        return queryset

    @action(detail=False, methods=["post"])
    def check_medication(self, request):
        """Check if a medication is safe for a patient based on allergies."""
        patient_id = request.data.get("patient_id")
        medication_id = request.data.get("medication_id")

        if not patient_id or not medication_id:
            return Response(
                {"error": "patient_id and medication_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get patient's active allergies
        allergies = PatientAllergy.objects.filter(
            patient_id=patient_id,
            is_active=True
        )

        # Check for direct medication allergy
        medication = MedicationCatalog.objects.get(id=medication_id)
        direct_allergy = allergies.filter(medication_id=medication_id).first()

        # Check for drug class allergy
        class_allergy = allergies.filter(
            allergen_type="drug_class",
            allergen_name__icontains=medication.drug_class
        ).first() if medication.drug_class else None

        warnings = []
        if direct_allergy:
            warnings.append({
                "type": "direct",
                "severity": direct_allergy.severity,
                "allergen": direct_allergy.allergen_name,
                "reaction": direct_allergy.reaction_description
            })

        if class_allergy:
            warnings.append({
                "type": "class",
                "severity": class_allergy.severity,
                "allergen": class_allergy.allergen_name,
                "reaction": class_allergy.reaction_description
            })

        return Response({
            "safe": len(warnings) == 0,
            "warnings": warnings,
            "medication": medication.generic_name
        })


class PrescriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for prescriptions."""

    queryset = Prescription.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return PrescriptionListSerializer
        if self.action == "create":
            return PrescriptionCreateSerializer
        return PrescriptionSerializer

    def get_queryset(self):
        queryset = Prescription.objects.all()

        # Filter by patient
        patient_id = self.request.query_params.get("patient_id")
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter active prescriptions
        active = self.request.query_params.get("active")
        if active is not None and active.lower() == "true":
            queryset = queryset.filter(status="active")

        # Filter by priority
        priority = self.request.query_params.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)

        # Filter by prescriber
        prescriber = self.request.query_params.get("prescriber")
        if prescriber:
            queryset = queryset.filter(prescriber_name__icontains=prescriber)

        return queryset.select_related("patient", "medication")

    def perform_create(self, serializer):
        # Generate prescription number
        prescription_number = f"RX-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Run safety checks
        patient = serializer.validated_data["patient"]
        medication = serializer.validated_data["medication"]

        # Check allergies
        allergy_warnings = []
        allergies = PatientAllergy.objects.filter(patient=patient, is_active=True)

        direct_allergy = allergies.filter(medication=medication).first()
        if direct_allergy:
            allergy_warnings.append({
                "type": "direct",
                "severity": direct_allergy.severity,
                "allergen": direct_allergy.allergen_name
            })

        allergy_check_passed = len(allergy_warnings) == 0

        # Check drug interactions with current medications
        active_prescriptions = Prescription.objects.filter(
            patient=patient,
            status="active"
        ).values_list("medication_id", flat=True)

        interaction_warnings = []
        if active_prescriptions:
            interactions = DrugInteraction.objects.filter(
                Q(drug_a=medication, drug_b_id__in=active_prescriptions) |
                Q(drug_b=medication, drug_a_id__in=active_prescriptions)
            )

            for interaction in interactions:
                other_drug = interaction.drug_a if interaction.drug_b == medication else interaction.drug_b
                interaction_warnings.append({
                    "severity": interaction.severity,
                    "drug": other_drug.generic_name,
                    "description": interaction.description
                })

        interaction_check_passed = not any(
            w["severity"] in ["major", "contraindicated"]
            for w in interaction_warnings
        )

        # Set refills remaining to allowed
        refills_allowed = serializer.validated_data.get("refills_allowed", 0)

        serializer.save(
            prescription_number=prescription_number,
            status="pending",  # Start as pending for review
            allergy_check_passed=allergy_check_passed,
            interaction_check_passed=interaction_check_passed,
            interaction_warnings=interaction_warnings,
            refills_remaining=refills_allowed
        )

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate a prescription after review."""
        prescription = self.get_object()

        if prescription.status not in ["draft", "pending"]:
            return Response(
                {"error": f"Cannot activate prescription with status '{prescription.status}'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        prescription.status = "active"
        prescription.save()

        # Generate scheduled administrations
        self._generate_administrations(prescription)

        return Response(PrescriptionSerializer(prescription).data)

    @action(detail=True, methods=["post"])
    def hold(self, request, pk=None):
        """Place a prescription on hold."""
        prescription = self.get_object()

        if prescription.status != "active":
            return Response(
                {"error": "Can only hold active prescriptions"},
                status=status.HTTP_400_BAD_REQUEST
            )

        prescription.status = "on_hold"
        prescription.hold_reason = request.data.get("reason", "")
        prescription.held_at = timezone.now()
        prescription.held_by = request.data.get("held_by", "")
        prescription.save()

        return Response(PrescriptionSerializer(prescription).data)

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        """Resume a held prescription."""
        prescription = self.get_object()

        if prescription.status != "on_hold":
            return Response(
                {"error": "Can only resume held prescriptions"},
                status=status.HTTP_400_BAD_REQUEST
            )

        prescription.status = "active"
        prescription.hold_reason = ""
        prescription.held_at = None
        prescription.held_by = ""
        prescription.save()

        return Response(PrescriptionSerializer(prescription).data)

    @action(detail=True, methods=["post"])
    def discontinue(self, request, pk=None):
        """Discontinue a prescription."""
        prescription = self.get_object()

        if prescription.status in ["completed", "cancelled", "discontinued"]:
            return Response(
                {"error": f"Cannot discontinue prescription with status '{prescription.status}'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        prescription.status = "discontinued"
        prescription.discontinued_reason = request.data.get("reason", "")
        prescription.discontinued_at = timezone.now()
        prescription.discontinued_by = request.data.get("discontinued_by", "")
        prescription.save()

        # Cancel pending administrations
        MedicationAdministration.objects.filter(
            prescription=prescription,
            status="scheduled"
        ).update(status="missed", not_given_reason="held_per_provider")

        return Response(PrescriptionSerializer(prescription).data)

    def _generate_administrations(self, prescription):
        """Generate scheduled medication administrations."""
        if not prescription.start_date:
            return

        start = datetime.combine(prescription.start_date, datetime.min.time())
        start = timezone.make_aware(start)

        # Determine end date
        if prescription.end_date:
            end = datetime.combine(prescription.end_date, datetime.max.time())
            end = timezone.make_aware(end)
        elif prescription.duration_days:
            end = start + timedelta(days=prescription.duration_days)
        else:
            # Default to 7 days if no end specified
            end = start + timedelta(days=7)

        # Parse frequency
        frequency = prescription.frequency.upper()
        hours_between = prescription.frequency_hours

        if not hours_between:
            # Common frequencies
            freq_map = {
                "DAILY": 24,
                "QD": 24,
                "BID": 12,
                "TID": 8,
                "QID": 6,
                "Q4H": 4,
                "Q6H": 6,
                "Q8H": 8,
                "Q12H": 12,
            }

            for freq_key, hours in freq_map.items():
                if freq_key in frequency:
                    hours_between = hours
                    break

        if not hours_between:
            hours_between = 24  # Default to daily

        # Skip PRN medications (they're given as needed)
        if "PRN" in frequency:
            return

        # Generate administrations
        current = start
        administrations = []

        while current <= end:
            administrations.append(
                MedicationAdministration(
                    prescription=prescription,
                    scheduled_time=current,
                    status="scheduled"
                )
            )
            current += timedelta(hours=hours_between)

        MedicationAdministration.objects.bulk_create(administrations)


class MedicationAdministrationViewSet(viewsets.ModelViewSet):
    """ViewSet for medication administrations (MAR)."""

    queryset = MedicationAdministration.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return MedicationAdministrationListSerializer
        return MedicationAdministrationSerializer

    def get_queryset(self):
        queryset = MedicationAdministration.objects.all()

        # Filter by prescription
        prescription_id = self.request.query_params.get("prescription_id")
        if prescription_id:
            queryset = queryset.filter(prescription_id=prescription_id)

        # Filter by patient (through prescription)
        patient_id = self.request.query_params.get("patient_id")
        if patient_id:
            queryset = queryset.filter(prescription__patient_id=patient_id)

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by date range
        date_from = self.request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(scheduled_time__date__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(scheduled_time__date__lte=date_to)

        # Filter due/overdue
        due = self.request.query_params.get("due")
        if due is not None and due.lower() == "true":
            now = timezone.now()
            queryset = queryset.filter(
                status="scheduled",
                scheduled_time__lte=now + timedelta(hours=1)
            )

        return queryset.select_related("prescription__patient", "prescription__medication")

    @action(detail=True, methods=["post"])
    def administer(self, request, pk=None):
        """Record medication administration."""
        administration = self.get_object()

        if administration.status != "scheduled":
            return Response(
                {"error": f"Cannot administer medication with status '{administration.status}'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update administration record
        administration.status = "given"
        administration.administered_at = timezone.now()
        administration.administered_by = request.data.get("administered_by", "")
        administration.administered_by_id = request.data.get("administered_by_id", "")
        administration.dose_given = request.data.get(
            "dose_given",
            administration.prescription.dose_quantity
        )
        administration.dose_unit = request.data.get(
            "dose_unit",
            administration.prescription.dose_unit
        )
        administration.route_given = request.data.get(
            "route_given",
            administration.prescription.route
        )
        administration.site = request.data.get("site", "")
        administration.witness_name = request.data.get("witness_name", "")
        administration.witness_id = request.data.get("witness_id", "")
        administration.patient_response = request.data.get("patient_response", "")
        administration.vital_signs_before = request.data.get("vital_signs_before", {})
        administration.vital_signs_after = request.data.get("vital_signs_after", {})
        administration.notes = request.data.get("notes", "")
        administration.save()

        return Response(MedicationAdministrationSerializer(administration).data)

    @action(detail=True, methods=["post"])
    def not_given(self, request, pk=None):
        """Record medication not given."""
        administration = self.get_object()

        if administration.status != "scheduled":
            return Response(
                {"error": f"Cannot update medication with status '{administration.status}'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        reason = request.data.get("reason")
        if not reason:
            return Response(
                {"error": "Reason is required when medication is not given"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Map common reasons
        if reason == "refused":
            administration.status = "refused"
        elif reason == "held":
            administration.status = "held"
        else:
            administration.status = "not_given"

        administration.not_given_reason = reason
        administration.not_given_details = request.data.get("details", "")
        administration.administered_by = request.data.get("documented_by", "")
        administration.notes = request.data.get("notes", "")
        administration.save()

        return Response(MedicationAdministrationSerializer(administration).data)


class PatientMedicationHistoryView(APIView):
    """View patient's complete medication history."""

    def get(self, request, patient_id):
        # Get all prescriptions for patient
        prescriptions = Prescription.objects.filter(
            patient_id=patient_id
        ).select_related("medication").order_by("-prescribed_at")

        # Get allergies
        allergies = PatientAllergy.objects.filter(
            patient_id=patient_id,
            is_active=True
        )

        # Get recent administrations
        recent_administrations = MedicationAdministration.objects.filter(
            prescription__patient_id=patient_id
        ).select_related(
            "prescription__medication"
        ).order_by("-scheduled_time")[:50]

        return Response({
            "prescriptions": {
                "active": PrescriptionListSerializer(
                    prescriptions.filter(status="active"), many=True
                ).data,
                "on_hold": PrescriptionListSerializer(
                    prescriptions.filter(status="on_hold"), many=True
                ).data,
                "completed": PrescriptionListSerializer(
                    prescriptions.filter(status__in=["completed", "discontinued"]), many=True
                ).data,
            },
            "allergies": PatientAllergySerializer(allergies, many=True).data,
            "recent_administrations": MedicationAdministrationListSerializer(
                recent_administrations, many=True
            ).data,
        })


class MedicationStatsView(APIView):
    """Get medication statistics."""

    def get(self, request):
        now = timezone.now()
        today = now.date()

        # Prescription stats
        total_prescriptions = Prescription.objects.count()
        active_prescriptions = Prescription.objects.filter(status="active").count()
        pending_prescriptions = Prescription.objects.filter(status="pending").count()

        # Administration stats for today
        today_administrations = MedicationAdministration.objects.filter(
            scheduled_time__date=today
        )
        due_now = today_administrations.filter(
            status="scheduled",
            scheduled_time__lte=now + timedelta(hours=1)
        ).count()
        given_today = today_administrations.filter(status="given").count()
        missed_today = today_administrations.filter(
            status__in=["missed", "not_given"]
        ).count()

        # High-alert medication stats
        high_alert_active = Prescription.objects.filter(
            status="active",
            medication__is_high_alert=True
        ).count()

        # Controlled substance stats
        controlled_active = Prescription.objects.filter(
            status="active",
            medication__is_controlled=True
        ).count()

        # Category breakdown
        category_stats = Prescription.objects.filter(
            status="active"
        ).values(
            "medication__category"
        ).annotate(
            count=Count("id")
        ).order_by("-count")

        return Response({
            "prescriptions": {
                "total": total_prescriptions,
                "active": active_prescriptions,
                "pending_review": pending_prescriptions,
                "high_alert_active": high_alert_active,
                "controlled_active": controlled_active,
            },
            "administrations_today": {
                "due_now": due_now,
                "given": given_today,
                "missed": missed_today,
                "total_scheduled": today_administrations.filter(status="scheduled").count(),
            },
            "category_breakdown": [
                {"category": item["medication__category"], "count": item["count"]}
                for item in category_stats
            ],
            "catalog_size": MedicationCatalog.objects.filter(is_active=True).count(),
        })
