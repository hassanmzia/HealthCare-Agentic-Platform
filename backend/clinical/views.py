from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
import hashlib
import json
from datetime import timedelta

from patients.models import Patient
from .models import (
    Encounter, ClinicalNote, Diagnosis, CarePlan, Vitals,
    ClinicalAssessment, PhysicianReview, AssessmentAuditLog,
    ClinicalDocument, EHROrder
)
from .serializers import (
    EncounterListSerializer, EncounterDetailSerializer,
    ClinicalNoteListSerializer, ClinicalNoteDetailSerializer,
    DiagnosisSerializer,
    CarePlanListSerializer, CarePlanDetailSerializer,
    VitalsSerializer,
    PatientClinicalSummarySerializer,
    ClinicalAssessmentListSerializer, ClinicalAssessmentDetailSerializer,
    ClinicalAssessmentCreateSerializer,
    PhysicianReviewListSerializer, PhysicianReviewDetailSerializer,
    PhysicianReviewSubmitSerializer,
    AssessmentAuditLogSerializer,
    ClinicalDocumentSerializer, DocumentGenerateSerializer,
    EHROrderSerializer, EHROrderCreateSerializer,
)


# Encounter Views
class EncounterListView(APIView):
    """List encounters with filtering, or create a new encounter."""

    def get(self, request):
        encounters = Encounter.objects.all()

        # Filter by patient
        patient_id = request.query_params.get("patient")
        if patient_id:
            encounters = encounters.filter(patient_id=patient_id)

        # Filter by status
        enc_status = request.query_params.get("status")
        if enc_status:
            encounters = encounters.filter(status=enc_status)

        # Filter by type
        enc_type = request.query_params.get("type")
        if enc_type:
            encounters = encounters.filter(encounter_type=enc_type)

        # Filter by physician
        physician = request.query_params.get("physician")
        if physician:
            encounters = encounters.filter(attending_physician__icontains=physician)

        # Date range filtering
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        if start_date:
            encounters = encounters.filter(start_time__date__gte=start_date)
        if end_date:
            encounters = encounters.filter(start_time__date__lte=end_date)

        # Pagination
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))

        total = encounters.count()
        encounters = encounters[offset:offset + limit]

        serializer = EncounterListSerializer(encounters, many=True)
        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": serializer.data
        })

    def post(self, request):
        serializer = EncounterDetailSerializer(data=request.data)
        if serializer.is_valid():
            encounter = serializer.save()
            return Response(EncounterDetailSerializer(encounter).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EncounterDetailView(APIView):
    """Get, update, or delete a specific encounter."""

    def get(self, request, encounter_id):
        encounter = get_object_or_404(Encounter, id=encounter_id)
        serializer = EncounterDetailSerializer(encounter)
        return Response(serializer.data)

    def put(self, request, encounter_id):
        encounter = get_object_or_404(Encounter, id=encounter_id)
        serializer = EncounterDetailSerializer(encounter, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, encounter_id):
        encounter = get_object_or_404(Encounter, id=encounter_id)
        encounter.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Clinical Note Views
class ClinicalNoteListView(APIView):
    """List clinical notes with filtering, or create a new note."""

    def get(self, request):
        notes = ClinicalNote.objects.all()

        # Filter by patient
        patient_id = request.query_params.get("patient")
        if patient_id:
            notes = notes.filter(patient_id=patient_id)

        # Filter by encounter
        encounter_id = request.query_params.get("encounter")
        if encounter_id:
            notes = notes.filter(encounter_id=encounter_id)

        # Filter by type
        note_type = request.query_params.get("type")
        if note_type:
            notes = notes.filter(note_type=note_type)

        # Filter by status
        note_status = request.query_params.get("status")
        if note_status:
            notes = notes.filter(status=note_status)

        # Filter by author
        author = request.query_params.get("author")
        if author:
            notes = notes.filter(author__icontains=author)

        # Pagination
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))

        total = notes.count()
        notes = notes[offset:offset + limit]

        serializer = ClinicalNoteListSerializer(notes, many=True)
        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": serializer.data
        })

    def post(self, request):
        serializer = ClinicalNoteDetailSerializer(data=request.data)
        if serializer.is_valid():
            note = serializer.save()
            return Response(ClinicalNoteDetailSerializer(note).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClinicalNoteDetailView(APIView):
    """Get, update, or delete a specific clinical note."""

    def get(self, request, note_id):
        note = get_object_or_404(ClinicalNote, id=note_id)
        serializer = ClinicalNoteDetailSerializer(note)
        return Response(serializer.data)

    def put(self, request, note_id):
        note = get_object_or_404(ClinicalNote, id=note_id)
        serializer = ClinicalNoteDetailSerializer(note, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, note_id):
        note = get_object_or_404(ClinicalNote, id=note_id)
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SignNoteView(APIView):
    """Sign a clinical note (finalize it)."""

    def post(self, request, note_id):
        note = get_object_or_404(ClinicalNote, id=note_id)

        if note.status == "final":
            return Response({"error": "Note is already signed"}, status=status.HTTP_400_BAD_REQUEST)

        co_signer = request.data.get("co_signer", "")
        note.status = "final"
        note.signed_datetime = timezone.now()
        if co_signer:
            note.co_signer = co_signer
        note.save()

        return Response(ClinicalNoteDetailSerializer(note).data)


# Diagnosis Views
class DiagnosisListView(APIView):
    """List diagnoses with filtering, or create a new diagnosis."""

    def get(self, request):
        diagnoses = Diagnosis.objects.all()

        # Filter by patient
        patient_id = request.query_params.get("patient")
        if patient_id:
            diagnoses = diagnoses.filter(patient_id=patient_id)

        # Filter by encounter
        encounter_id = request.query_params.get("encounter")
        if encounter_id:
            diagnoses = diagnoses.filter(encounter_id=encounter_id)

        # Filter by status
        dx_status = request.query_params.get("status")
        if dx_status:
            diagnoses = diagnoses.filter(status=dx_status)

        # Filter by ICD-10 code
        icd10 = request.query_params.get("icd10")
        if icd10:
            diagnoses = diagnoses.filter(icd10_code__icontains=icd10)

        # Pagination
        limit = int(request.query_params.get("limit", 100))
        offset = int(request.query_params.get("offset", 0))

        total = diagnoses.count()
        diagnoses = diagnoses[offset:offset + limit]

        serializer = DiagnosisSerializer(diagnoses, many=True)
        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": serializer.data
        })

    def post(self, request):
        serializer = DiagnosisSerializer(data=request.data)
        if serializer.is_valid():
            diagnosis = serializer.save()
            return Response(DiagnosisSerializer(diagnosis).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DiagnosisDetailView(APIView):
    """Get, update, or delete a specific diagnosis."""

    def get(self, request, diagnosis_id):
        diagnosis = get_object_or_404(Diagnosis, id=diagnosis_id)
        serializer = DiagnosisSerializer(diagnosis)
        return Response(serializer.data)

    def put(self, request, diagnosis_id):
        diagnosis = get_object_or_404(Diagnosis, id=diagnosis_id)
        serializer = DiagnosisSerializer(diagnosis, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, diagnosis_id):
        diagnosis = get_object_or_404(Diagnosis, id=diagnosis_id)
        diagnosis.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Care Plan Views
class CarePlanListView(APIView):
    """List care plans with filtering, or create a new care plan."""

    def get(self, request):
        plans = CarePlan.objects.all()

        # Filter by patient
        patient_id = request.query_params.get("patient")
        if patient_id:
            plans = plans.filter(patient_id=patient_id)

        # Filter by status
        plan_status = request.query_params.get("status")
        if plan_status:
            plans = plans.filter(status=plan_status)

        # Filter by category
        category = request.query_params.get("category")
        if category:
            plans = plans.filter(category=category)

        # Pagination
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))

        total = plans.count()
        plans = plans[offset:offset + limit]

        serializer = CarePlanListSerializer(plans, many=True)
        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": serializer.data
        })

    def post(self, request):
        serializer = CarePlanDetailSerializer(data=request.data)
        if serializer.is_valid():
            plan = serializer.save()
            return Response(CarePlanDetailSerializer(plan).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CarePlanDetailView(APIView):
    """Get, update, or delete a specific care plan."""

    def get(self, request, plan_id):
        plan = get_object_or_404(CarePlan, id=plan_id)
        serializer = CarePlanDetailSerializer(plan)
        return Response(serializer.data)

    def put(self, request, plan_id):
        plan = get_object_or_404(CarePlan, id=plan_id)
        serializer = CarePlanDetailSerializer(plan, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, plan_id):
        plan = get_object_or_404(CarePlan, id=plan_id)
        plan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Vitals Views
class VitalsListView(APIView):
    """List vitals with filtering, or record new vitals."""

    def get(self, request):
        vitals = Vitals.objects.all()

        # Filter by patient
        patient_id = request.query_params.get("patient")
        if patient_id:
            vitals = vitals.filter(patient_id=patient_id)

        # Filter by encounter
        encounter_id = request.query_params.get("encounter")
        if encounter_id:
            vitals = vitals.filter(encounter_id=encounter_id)

        # Date range
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        if start_date:
            vitals = vitals.filter(recorded_at__date__gte=start_date)
        if end_date:
            vitals = vitals.filter(recorded_at__date__lte=end_date)

        # Pagination
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))

        total = vitals.count()
        vitals = vitals[offset:offset + limit]

        serializer = VitalsSerializer(vitals, many=True)
        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": serializer.data
        })

    def post(self, request):
        serializer = VitalsSerializer(data=request.data)
        if serializer.is_valid():
            vitals = serializer.save()
            return Response(VitalsSerializer(vitals).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VitalsDetailView(APIView):
    """Get or delete a specific vitals record."""

    def get(self, request, vitals_id):
        vitals = get_object_or_404(Vitals, id=vitals_id)
        serializer = VitalsSerializer(vitals)
        return Response(serializer.data)

    def delete(self, request, vitals_id):
        vitals = get_object_or_404(Vitals, id=vitals_id)
        vitals.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Patient Clinical Summary
class PatientClinicalSummaryView(APIView):
    """Get comprehensive clinical summary for a patient."""

    def get(self, request, patient_id):
        patient = get_object_or_404(Patient, id=patient_id)

        # Get active encounters
        active_encounters = Encounter.objects.filter(
            patient=patient,
            status__in=["in_progress", "on_hold", "planned"]
        ).order_by("-start_time")[:5]

        # Get recent notes
        recent_notes = ClinicalNote.objects.filter(
            patient=patient
        ).order_by("-note_datetime")[:10]

        # Get active diagnoses
        active_diagnoses = Diagnosis.objects.filter(
            patient=patient,
            status="active"
        ).order_by("rank")

        # Get active care plans
        active_care_plans = CarePlan.objects.filter(
            patient=patient,
            status="active"
        )

        # Get latest vitals
        latest_vitals = Vitals.objects.filter(patient=patient).first()

        summary_data = {
            "patient_id": patient.id,
            "patient_name": patient.full_name,
            "patient_mrn": patient.mrn,
            "age": patient.age,
            "gender": patient.gender,
            "active_encounters": EncounterListSerializer(active_encounters, many=True).data,
            "recent_notes": ClinicalNoteListSerializer(recent_notes, many=True).data,
            "active_diagnoses": DiagnosisSerializer(active_diagnoses, many=True).data,
            "active_care_plans": CarePlanListSerializer(active_care_plans, many=True).data,
            "latest_vitals": VitalsSerializer(latest_vitals).data if latest_vitals else None,
            "allergies": patient.allergies or [],
            "medications": patient.medications or [],
        }

        return Response(summary_data)


# =============================================================================
# AI Clinical Assessment Views
# =============================================================================

class ClinicalAssessmentListView(APIView):
    """List clinical assessments with filtering, or create a new assessment."""

    def get(self, request):
        assessments = ClinicalAssessment.objects.all()

        # Filter by patient
        patient_id = request.query_params.get("patient")
        if patient_id:
            assessments = assessments.filter(patient_id=patient_id)

        # Filter by status
        assessment_status = request.query_params.get("status")
        if assessment_status:
            assessments = assessments.filter(status=assessment_status)

        # Filter pending reviews only
        if request.query_params.get("pending_review") == "true":
            assessments = assessments.filter(status__in=["pending", "in_review"])

        # Filter by requires_human_review
        if request.query_params.get("requires_review") == "true":
            assessments = assessments.filter(requires_human_review=True)

        # Filter by encounter
        encounter_id = request.query_params.get("encounter")
        if encounter_id:
            assessments = assessments.filter(encounter_id=encounter_id)

        # Date range
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        if start_date:
            assessments = assessments.filter(assessment_datetime__date__gte=start_date)
        if end_date:
            assessments = assessments.filter(assessment_datetime__date__lte=end_date)

        # Pagination
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))

        total = assessments.count()
        assessments = assessments[offset:offset + limit]

        serializer = ClinicalAssessmentListSerializer(assessments, many=True)
        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": serializer.data
        })

    def post(self, request):
        """Create a new clinical assessment (typically from orchestrator)."""
        serializer = ClinicalAssessmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Set expiration (24 hours by default)
            expires_at = timezone.now() + timedelta(hours=24)

            # Extract primary diagnosis
            diagnoses = serializer.validated_data.get("diagnoses", [])
            primary_code = ""
            primary_desc = ""
            if diagnoses:
                primary = diagnoses[0]
                primary_code = primary.get("icd10_code", "")
                primary_desc = primary.get("diagnosis", "")

            assessment = serializer.save(
                expires_at=expires_at,
                primary_diagnosis_code=primary_code,
                primary_diagnosis_description=primary_desc
            )

            # Create audit log entry
            self._create_audit_log(
                assessment=assessment,
                action="created",
                actor_id="system",
                actor_name="AI Orchestrator",
                actor_role="system",
                request=request
            )

            return Response(
                ClinicalAssessmentDetailSerializer(assessment).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _create_audit_log(self, assessment, action, actor_id, actor_name, actor_role, request, detail=""):
        AssessmentAuditLog.objects.create(
            assessment=assessment,
            action=action,
            action_detail=detail,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_role=actor_role,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500]
        )

    def _get_client_ip(self, request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


class ClinicalAssessmentDetailView(APIView):
    """Get or update a specific clinical assessment."""

    def get(self, request, assessment_id):
        assessment = get_object_or_404(ClinicalAssessment, id=assessment_id)

        # Log view action
        actor_id = request.query_params.get("viewer_id", "unknown")
        actor_name = request.query_params.get("viewer_name", "Unknown")

        AssessmentAuditLog.objects.create(
            assessment=assessment,
            action="viewed",
            actor_id=actor_id,
            actor_name=actor_name,
            actor_role=request.query_params.get("viewer_role", ""),
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500]
        )

        serializer = ClinicalAssessmentDetailSerializer(assessment)
        return Response(serializer.data)

    def put(self, request, assessment_id):
        assessment = get_object_or_404(ClinicalAssessment, id=assessment_id)
        previous_state = {"status": assessment.status}

        serializer = ClinicalAssessmentDetailSerializer(
            assessment, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()

            # Log modification
            AssessmentAuditLog.objects.create(
                assessment=assessment,
                action="modified",
                actor_id=request.data.get("modifier_id", "unknown"),
                actor_name=request.data.get("modifier_name", "Unknown"),
                actor_role=request.data.get("modifier_role", ""),
                previous_state=previous_state,
                new_state={"status": assessment.status},
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500]
            )

            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _get_client_ip(self, request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


# =============================================================================
# Physician Review Views
# =============================================================================

class PhysicianReviewListView(APIView):
    """List physician reviews with filtering."""

    def get(self, request):
        reviews = PhysicianReview.objects.all()

        # Filter by assessment
        assessment_id = request.query_params.get("assessment")
        if assessment_id:
            reviews = reviews.filter(assessment_id=assessment_id)

        # Filter by physician
        physician_id = request.query_params.get("physician")
        if physician_id:
            reviews = reviews.filter(physician_id=physician_id)

        # Filter by decision
        decision = request.query_params.get("decision")
        if decision:
            reviews = reviews.filter(decision=decision)

        # Pagination
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))

        total = reviews.count()
        reviews = reviews[offset:offset + limit]

        serializer = PhysicianReviewListSerializer(reviews, many=True)
        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": serializer.data
        })


class PhysicianReviewSubmitView(APIView):
    """Submit a physician review for an assessment."""

    @transaction.atomic
    def post(self, request):
        serializer = PhysicianReviewSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        assessment = get_object_or_404(ClinicalAssessment, id=data["assessment_id"])

        # Check if assessment is still valid
        if assessment.is_expired():
            return Response(
                {"error": "Assessment has expired and cannot be reviewed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate review time
        review_started_at = data.get("review_started_at")
        review_completed_at = timezone.now()
        time_spent = 0
        if review_started_at:
            time_spent = int((review_completed_at - review_started_at).total_seconds())

        # Build final codes based on approvals
        final_icd10 = self._build_final_codes(
            assessment.icd10_codes,
            data.get("approved_diagnoses", []),
            data.get("rejected_diagnoses", []),
            data.get("added_diagnoses", [])
        )
        final_cpt = self._build_final_codes(
            assessment.cpt_codes,
            data.get("approved_treatments", []),
            data.get("rejected_treatments", []),
            data.get("added_treatments", [])
        )

        # Generate digital signature
        signature_data = {
            "assessment_id": str(assessment.id),
            "physician_id": data["physician_id"],
            "decision": data["decision"],
            "timestamp": review_completed_at.isoformat()
        }
        digital_signature = hashlib.sha256(
            json.dumps(signature_data, sort_keys=True).encode()
        ).hexdigest()

        # Create the review
        review = PhysicianReview.objects.create(
            assessment=assessment,
            physician_id=data["physician_id"],
            physician_name=data["physician_name"],
            physician_npi=data.get("physician_npi", ""),
            physician_specialty=data.get("physician_specialty", ""),
            decision=data["decision"],
            approved_diagnoses=data.get("approved_diagnoses", []),
            rejected_diagnoses=data.get("rejected_diagnoses", []),
            approved_treatments=data.get("approved_treatments", []),
            rejected_treatments=data.get("rejected_treatments", []),
            modified_diagnoses=data.get("modified_diagnoses", []),
            modified_treatments=data.get("modified_treatments", []),
            added_diagnoses=data.get("added_diagnoses", []),
            added_treatments=data.get("added_treatments", []),
            final_icd10_codes=final_icd10,
            final_cpt_codes=final_cpt,
            physician_notes=data.get("physician_notes", ""),
            rejection_reason=data.get("rejection_reason", ""),
            clinical_rationale=data.get("clinical_rationale", ""),
            attested=data.get("attest", False),
            digital_signature=digital_signature,
            signature_datetime=review_completed_at if data.get("attest") else None,
            review_started_at=review_started_at,
            review_completed_at=review_completed_at,
            time_spent_seconds=time_spent,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500]
        )

        # Update assessment status
        status_map = {
            "approved": "approved",
            "approved_modified": "modified",
            "rejected": "rejected",
            "deferred": "in_review"
        }
        assessment.status = status_map.get(data["decision"], "pending")
        assessment.save()

        # Create audit log entries
        self._create_review_audit_logs(assessment, review, data, request)

        return Response(
            PhysicianReviewDetailSerializer(review).data,
            status=status.HTTP_201_CREATED
        )

    def _build_final_codes(self, original_codes, approved_indices, rejected_indices, added_items):
        """Build final code list based on approvals/rejections."""
        final = []
        for i, code in enumerate(original_codes):
            if i in rejected_indices:
                continue
            if i in approved_indices or not approved_indices:  # If no specific approvals, include all non-rejected
                final.append(code)

        # Add physician-added items
        for item in added_items:
            if "code" in item:
                final.append({"code": item["code"], "description": item.get("description", "")})
            elif "icd10_code" in item:
                final.append({"code": item["icd10_code"], "description": item.get("diagnosis", "")})

        return final

    def _create_review_audit_logs(self, assessment, review, data, request):
        """Create detailed audit logs for the review."""
        ip = self._get_client_ip(request)
        ua = request.META.get("HTTP_USER_AGENT", "")[:500]

        # Main review completed log
        AssessmentAuditLog.objects.create(
            assessment=assessment,
            physician_review=review,
            action="review_completed",
            action_detail=f"Review completed with decision: {data['decision']}",
            actor_id=data["physician_id"],
            actor_name=data["physician_name"],
            actor_role="physician",
            new_state={"decision": data["decision"], "attested": data.get("attest", False)},
            ip_address=ip,
            user_agent=ua
        )

        # Log individual diagnosis decisions
        for i in data.get("approved_diagnoses", []):
            if i < len(assessment.diagnoses):
                dx = assessment.diagnoses[i]
                AssessmentAuditLog.objects.create(
                    assessment=assessment,
                    physician_review=review,
                    action="diagnosis_approved",
                    action_detail=f"Diagnosis approved: {dx.get('diagnosis', '')}",
                    actor_id=data["physician_id"],
                    actor_name=data["physician_name"],
                    actor_role="physician",
                    related_item_type="diagnosis",
                    related_item_id=str(i),
                    related_item_detail=dx,
                    ip_address=ip,
                    user_agent=ua
                )

        for i in data.get("rejected_diagnoses", []):
            if i < len(assessment.diagnoses):
                dx = assessment.diagnoses[i]
                AssessmentAuditLog.objects.create(
                    assessment=assessment,
                    physician_review=review,
                    action="diagnosis_rejected",
                    action_detail=f"Diagnosis rejected: {dx.get('diagnosis', '')}",
                    actor_id=data["physician_id"],
                    actor_name=data["physician_name"],
                    actor_role="physician",
                    related_item_type="diagnosis",
                    related_item_id=str(i),
                    related_item_detail=dx,
                    ip_address=ip,
                    user_agent=ua
                )

        # Log added diagnoses
        for dx in data.get("added_diagnoses", []):
            AssessmentAuditLog.objects.create(
                assessment=assessment,
                physician_review=review,
                action="diagnosis_added",
                action_detail=f"Diagnosis added by physician: {dx.get('diagnosis', '')}",
                actor_id=data["physician_id"],
                actor_name=data["physician_name"],
                actor_role="physician",
                related_item_type="diagnosis",
                related_item_detail=dx,
                ip_address=ip,
                user_agent=ua
            )

        # Similar logs for treatments...
        for i in data.get("approved_treatments", []):
            if i < len(assessment.treatments):
                tx = assessment.treatments[i]
                AssessmentAuditLog.objects.create(
                    assessment=assessment,
                    physician_review=review,
                    action="treatment_approved",
                    actor_id=data["physician_id"],
                    actor_name=data["physician_name"],
                    actor_role="physician",
                    related_item_type="treatment",
                    related_item_id=str(i),
                    related_item_detail=tx,
                    ip_address=ip,
                    user_agent=ua
                )

    def _get_client_ip(self, request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


class PhysicianReviewDetailView(APIView):
    """Get details of a specific physician review."""

    def get(self, request, review_id):
        review = get_object_or_404(PhysicianReview, id=review_id)
        serializer = PhysicianReviewDetailSerializer(review)
        return Response(serializer.data)


# =============================================================================
# Audit Log Views
# =============================================================================

class AssessmentAuditLogView(APIView):
    """Get audit logs for an assessment."""

    def get(self, request, assessment_id):
        assessment = get_object_or_404(ClinicalAssessment, id=assessment_id)
        logs = assessment.audit_logs.all()

        # Filter by action
        action = request.query_params.get("action")
        if action:
            logs = logs.filter(action=action)

        # Filter by actor
        actor_id = request.query_params.get("actor")
        if actor_id:
            logs = logs.filter(actor_id=actor_id)

        # Pagination
        limit = int(request.query_params.get("limit", 100))
        offset = int(request.query_params.get("offset", 0))

        total = logs.count()
        logs = logs[offset:offset + limit]

        serializer = AssessmentAuditLogSerializer(logs, many=True)
        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": serializer.data
        })


# =============================================================================
# Clinical Document Generation Views
# =============================================================================

class ClinicalDocumentListView(APIView):
    """List clinical documents."""

    def get(self, request):
        documents = ClinicalDocument.objects.all()

        # Filter by assessment
        assessment_id = request.query_params.get("assessment")
        if assessment_id:
            documents = documents.filter(assessment_id=assessment_id)

        # Filter by type
        doc_type = request.query_params.get("type")
        if doc_type:
            documents = documents.filter(document_type=doc_type)

        # Pagination
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))

        total = documents.count()
        documents = documents[offset:offset + limit]

        serializer = ClinicalDocumentSerializer(documents, many=True)
        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": serializer.data
        })


class GenerateDocumentView(APIView):
    """Generate clinical documentation from an approved assessment."""

    def post(self, request):
        serializer = DocumentGenerateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        assessment = get_object_or_404(ClinicalAssessment, id=data["assessment_id"])

        # Get the review if specified
        review = None
        if data.get("review_id"):
            review = get_object_or_404(PhysicianReview, id=data["review_id"])

        # Generate document content based on type
        doc_type = data["document_type"]
        content = self._generate_document_content(
            assessment, review, doc_type,
            include_reasoning=data.get("include_reasoning", False),
            include_codes=data.get("include_codes", True)
        )

        # Create document record
        document = ClinicalDocument.objects.create(
            assessment=assessment,
            physician_review=review,
            document_type=doc_type,
            title=f"{doc_type.replace('_', ' ').title()} - {assessment.patient.full_name}",
            format=data.get("format", "html"),
            status="final" if review and review.attested else "draft",
            content=content,
            structured_data=self._build_structured_data(assessment, review),
            generated_by="system",
            signed_by=review.physician_name if review and review.attested else "",
            signed_at=review.signature_datetime if review and review.attested else None
        )

        # Create audit log
        AssessmentAuditLog.objects.create(
            assessment=assessment,
            physician_review=review,
            action="documentation_generated",
            action_detail=f"Generated {doc_type} document",
            actor_id=request.data.get("generator_id", "system"),
            actor_name=request.data.get("generator_name", "System"),
            actor_role="system",
            related_item_type="document",
            related_item_id=str(document.id),
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500]
        )

        return Response(
            ClinicalDocumentSerializer(document).data,
            status=status.HTTP_201_CREATED
        )

    def _generate_document_content(self, assessment, review, doc_type, include_reasoning=False, include_codes=True):
        """Generate document content in HTML format."""
        patient = assessment.patient
        summary = assessment.patient_summary or {}

        # Use final codes if review exists, otherwise use assessment codes
        icd10_codes = review.final_icd10_codes if review else assessment.icd10_codes
        cpt_codes = review.final_cpt_codes if review else assessment.cpt_codes

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{doc_type.replace('_', ' ').title()}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 20px; }}
        .section {{ margin-bottom: 20px; }}
        .section-title {{ font-weight: bold; color: #333; margin-bottom: 10px; font-size: 14px; }}
        .finding {{ padding: 5px 0; border-bottom: 1px solid #eee; }}
        .critical {{ color: #dc3545; font-weight: bold; }}
        .warning {{ color: #ffc107; }}
        .code {{ font-family: monospace; background: #f5f5f5; padding: 2px 5px; }}
        .attestation {{ border: 1px solid #333; padding: 15px; margin-top: 30px; background: #f9f9f9; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{doc_type.replace('_', ' ').title()}</h1>
        <p><strong>Patient:</strong> {patient.full_name} (MRN: {patient.mrn})</p>
        <p><strong>DOB:</strong> {patient.date_of_birth or 'N/A'} | <strong>Age:</strong> {summary.get('age', 'N/A')} | <strong>Sex:</strong> {summary.get('sex', 'N/A')}</p>
        <p><strong>Assessment Date:</strong> {assessment.assessment_datetime.strftime('%Y-%m-%d %H:%M')}</p>
        <p><strong>Confidence Score:</strong> {assessment.confidence_score:.0%}</p>
    </div>
"""

        # Chief Complaint
        if assessment.chief_complaint:
            html += f"""
    <div class="section">
        <div class="section-title">CHIEF COMPLAINT</div>
        <p>{assessment.chief_complaint}</p>
    </div>
"""

        # History of Present Illness
        if assessment.history_present_illness:
            html += f"""
    <div class="section">
        <div class="section-title">HISTORY OF PRESENT ILLNESS</div>
        <p>{assessment.history_present_illness}</p>
    </div>
"""

        # Critical Findings
        if assessment.critical_findings:
            html += """
    <div class="section">
        <div class="section-title">CRITICAL FINDINGS</div>
"""
            for finding in assessment.critical_findings:
                html += f"""
        <div class="finding critical">
            <strong>{finding.get('name', 'N/A')}</strong>: {finding.get('value', 'N/A')} {finding.get('unit', '')}
            <br><em>{finding.get('interpretation', '')}</em>
        </div>
"""
            html += "    </div>\n"

        # All Findings
        if assessment.findings:
            html += """
    <div class="section">
        <div class="section-title">CLINICAL FINDINGS</div>
        <table>
            <tr><th>Finding</th><th>Value</th><th>Status</th><th>Interpretation</th></tr>
"""
            for finding in assessment.findings:
                status_class = "critical" if finding.get("status") == "critical" else ""
                html += f"""
            <tr class="{status_class}">
                <td>{finding.get('name', 'N/A')}</td>
                <td>{finding.get('value', 'N/A')} {finding.get('unit', '')}</td>
                <td>{finding.get('status', 'N/A')}</td>
                <td>{finding.get('interpretation', '')}</td>
            </tr>
"""
            html += "        </table>\n    </div>\n"

        # Diagnoses
        diagnoses = review.modified_diagnoses + review.added_diagnoses if review else assessment.diagnoses
        if diagnoses or assessment.diagnoses:
            html += """
    <div class="section">
        <div class="section-title">DIAGNOSES</div>
        <table>
            <tr><th>Diagnosis</th><th>ICD-10</th><th>Confidence</th></tr>
"""
            for dx in (diagnoses or assessment.diagnoses):
                html += f"""
            <tr>
                <td>{dx.get('diagnosis', 'N/A')}</td>
                <td class="code">{dx.get('icd10_code', 'N/A')}</td>
                <td>{dx.get('confidence', 0):.0%}</td>
            </tr>
"""
            html += "        </table>\n    </div>\n"

        # Treatment Plan
        treatments = review.modified_treatments + review.added_treatments if review else assessment.treatments
        if treatments or assessment.treatments:
            html += """
    <div class="section">
        <div class="section-title">TREATMENT PLAN</div>
        <table>
            <tr><th>Treatment</th><th>Priority</th><th>CPT Code</th></tr>
"""
            for tx in (treatments or assessment.treatments):
                html += f"""
            <tr>
                <td>{tx.get('description', 'N/A')}</td>
                <td>{tx.get('priority', 'routine')}</td>
                <td class="code">{tx.get('cpt_code', 'N/A')}</td>
            </tr>
"""
            html += "        </table>\n    </div>\n"

        # Coding Summary
        if include_codes:
            html += """
    <div class="section">
        <div class="section-title">CODING SUMMARY</div>
        <p><strong>ICD-10 Codes:</strong>
"""
            for code in icd10_codes:
                html += f'<span class="code">{code.get("code", "")}</span> ({code.get("description", "")}) '
            html += "</p>\n        <p><strong>CPT Codes:</strong>\n"
            for code in cpt_codes:
                html += f'<span class="code">{code.get("code", "")}</span> ({code.get("description", "")}) '
            html += "</p>\n    </div>\n"

        # Reasoning (if included)
        if include_reasoning and assessment.reasoning_chain:
            html += """
    <div class="section">
        <div class="section-title">AI REASONING CHAIN</div>
        <ol>
"""
            for step in assessment.reasoning_chain[-20:]:  # Last 20 steps
                html += f"            <li>{step}</li>\n"
            html += "        </ol>\n    </div>\n"

        # Attestation
        if review and review.attested:
            html += f"""
    <div class="attestation">
        <div class="section-title">PHYSICIAN ATTESTATION</div>
        <p>{review.attestation_statement}</p>
        <p><strong>Reviewed and Signed By:</strong> {review.physician_name}</p>
        <p><strong>NPI:</strong> {review.physician_npi or 'N/A'}</p>
        <p><strong>Specialty:</strong> {review.physician_specialty or 'N/A'}</p>
        <p><strong>Signature Date:</strong> {review.signature_datetime.strftime('%Y-%m-%d %H:%M') if review.signature_datetime else 'N/A'}</p>
        <p><strong>Digital Signature:</strong> <span class="code">{review.digital_signature[:32]}...</span></p>
    </div>
"""

        html += """
</body>
</html>
"""
        return html

    def _build_structured_data(self, assessment, review):
        """Build structured data for FHIR/CCD export."""
        return {
            "assessment_id": str(assessment.id),
            "patient_id": str(assessment.patient.id),
            "patient_mrn": assessment.patient.mrn,
            "assessment_datetime": assessment.assessment_datetime.isoformat(),
            "diagnoses": review.final_icd10_codes if review else assessment.icd10_codes,
            "procedures": review.final_cpt_codes if review else assessment.cpt_codes,
            "reviewed": bool(review),
            "attested": review.attested if review else False
        }

    def _get_client_ip(self, request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


class ClinicalDocumentDetailView(APIView):
    """Get a specific clinical document."""

    def get(self, request, document_id):
        document = get_object_or_404(ClinicalDocument, id=document_id)
        serializer = ClinicalDocumentSerializer(document)
        return Response(serializer.data)


# =============================================================================
# EHR Order Integration Views
# =============================================================================

class EHROrderListView(APIView):
    """List EHR orders with filtering."""

    def get(self, request):
        orders = EHROrder.objects.all()

        # Filter by patient
        patient_id = request.query_params.get("patient")
        if patient_id:
            orders = orders.filter(patient_id=patient_id)

        # Filter by assessment
        assessment_id = request.query_params.get("assessment")
        if assessment_id:
            orders = orders.filter(assessment_id=assessment_id)

        # Filter by status
        order_status = request.query_params.get("status")
        if order_status:
            orders = orders.filter(status=order_status)

        # Filter by type
        order_type = request.query_params.get("type")
        if order_type:
            orders = orders.filter(order_type=order_type)

        # Pagination
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))

        total = orders.count()
        orders = orders[offset:offset + limit]

        serializer = EHROrderSerializer(orders, many=True)
        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": serializer.data
        })


class CreateEHROrdersView(APIView):
    """Create EHR orders from approved treatments."""

    @transaction.atomic
    def post(self, request):
        serializer = EHROrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        assessment = get_object_or_404(ClinicalAssessment, id=data["assessment_id"])
        review = get_object_or_404(PhysicianReview, id=data["review_id"])

        if review.decision not in ["approved", "approved_modified"]:
            return Response(
                {"error": "Orders can only be created from approved assessments"},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_orders = []
        treatments = assessment.treatments

        for idx in data["treatment_indices"]:
            if idx >= len(treatments):
                continue

            treatment = treatments[idx]
            order_type = self._determine_order_type(treatment)

            order = EHROrder.objects.create(
                assessment=assessment,
                physician_review=review,
                patient=assessment.patient,
                order_type=order_type,
                status="pending",
                priority=treatment.get("priority") or "routine",
                description=treatment.get("description") or "",
                cpt_code=treatment.get("cpt_code") or "",
                order_details=treatment,
                indication=treatment.get("rationale") or "",
                icd10_codes=review.final_icd10_codes,
                ordering_physician_id=data["ordering_physician_id"],
                ordering_physician_name=data["ordering_physician_name"],
                ordering_physician_npi=data.get("ordering_physician_npi") or ""
            )

            # Extract specific fields based on order type
            self._populate_order_details(order, treatment)
            order.save()

            created_orders.append(order)

            # Create audit log
            AssessmentAuditLog.objects.create(
                assessment=assessment,
                physician_review=review,
                action="order_placed",
                action_detail=f"EHR order created: {treatment.get('description', '')}",
                actor_id=data["ordering_physician_id"],
                actor_name=data["ordering_physician_name"],
                actor_role="physician",
                related_item_type="order",
                related_item_id=str(order.id),
                related_item_detail=treatment,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500]
            )

        # Simulate EHR submission (in production, this would call actual EHR API)
        for order in created_orders:
            self._submit_to_ehr(order)

        return Response({
            "success": True,
            "orders_created": len(created_orders),
            "orders": EHROrderSerializer(created_orders, many=True).data
        }, status=status.HTTP_201_CREATED)

    def _determine_order_type(self, treatment):
        """Determine order type from treatment details."""
        desc_lower = (treatment.get("description") or "").lower()
        tx_type = (treatment.get("treatment_type") or treatment.get("type") or "").lower()

        if tx_type == "medication" or any(term in desc_lower for term in ["medication", "drug", "prescribe", "mg", "tablet"]):
            return "medication"
        elif any(term in desc_lower for term in ["lab", "blood test", "cbc", "bmp", "panel"]):
            return "lab"
        elif any(term in desc_lower for term in ["x-ray", "ct", "mri", "imaging", "scan", "ultrasound"]):
            return "imaging"
        elif tx_type == "referral" or "referral" in desc_lower or "consult" in desc_lower:
            return "referral"
        elif any(term in desc_lower for term in ["procedure", "biopsy", "surgery"]):
            return "procedure"
        else:
            return "procedure"

    def _populate_order_details(self, order, treatment):
        """Populate order-specific fields based on treatment type."""
        desc = treatment.get("description") or ""

        if order.order_type == "medication":
            # Try to extract medication details
            order.medication_name = desc.split(" - ")[0] if " - " in desc else desc[:200]

        elif order.order_type == "lab":
            order.test_name = desc[:200]

        elif order.order_type == "imaging":
            order.test_name = desc[:200]

        elif order.order_type == "referral":
            # Try to extract specialty
            for specialty in ["cardiology", "oncology", "gastroenterology", "neurology", "pulmonology"]:
                if specialty in desc.lower():
                    order.referral_specialty = specialty.title()
                    break
            order.referral_reason = treatment.get("rationale") or ""

    def _submit_to_ehr(self, order):
        """Submit order to EHR system (simulated)."""
        # In production, this would make an actual API call to the EHR
        # For now, we simulate acceptance
        order.status = "submitted"
        order.submitted_at = timezone.now()
        order.ehr_order_id = f"SIM-{order.id.hex[:8].upper()}"
        order.ehr_response = {
            "status": "accepted",
            "message": "Order submitted successfully (simulated)",
            "order_id": order.ehr_order_id
        }
        order.accepted_at = timezone.now()
        order.status = "accepted"
        order.save()

    def _get_client_ip(self, request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


class EHROrderDetailView(APIView):
    """Get details of a specific EHR order."""

    def get(self, request, order_id):
        order = get_object_or_404(EHROrder, id=order_id)
        serializer = EHROrderSerializer(order)
        return Response(serializer.data)
