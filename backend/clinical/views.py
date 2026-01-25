from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone

from patients.models import Patient
from .models import Encounter, ClinicalNote, Diagnosis, CarePlan, Vitals
from .serializers import (
    EncounterListSerializer, EncounterDetailSerializer,
    ClinicalNoteListSerializer, ClinicalNoteDetailSerializer,
    DiagnosisSerializer,
    CarePlanListSerializer, CarePlanDetailSerializer,
    VitalsSerializer,
    PatientClinicalSummarySerializer,
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
