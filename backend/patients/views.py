import uuid
import httpx
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Patient, PatientDocument
from .serializers import (
    PatientListSerializer,
    PatientDetailSerializer,
    PatientDocumentSerializer,
    PatientImportSerializer,
)

# FHIR server URL (same as used by MCP adapter)
FHIR_BASE = "http://hapi-fhir:8080/fhir"


def generate_mrn():
    """Generate a unique Medical Record Number."""
    return f"MRN-{uuid.uuid4().hex[:8].upper()}"


async def sync_patient_to_fhir(patient: Patient) -> str:
    """Create or update patient in FHIR server and return FHIR ID."""
    fhir_patient = {
        "resourceType": "Patient",
        "identifier": [
            {"system": "urn:mrn", "value": patient.mrn}
        ],
        "name": [{
            "use": "official",
            "family": patient.last_name,
            "given": [patient.first_name] + ([patient.middle_name] if patient.middle_name else []),
            "prefix": [patient.prefix] if patient.prefix else [],
            "suffix": [patient.suffix] if patient.suffix else [],
        }],
        "gender": patient.gender if patient.gender != "unknown" else "unknown",
        "birthDate": patient.date_of_birth.isoformat(),
        "active": patient.status == "active",
    }

    # Add telecom if available
    telecom = []
    if patient.phone:
        telecom.append({"system": "phone", "value": patient.phone, "use": "home"})
    if patient.email:
        telecom.append({"system": "email", "value": patient.email})
    if telecom:
        fhir_patient["telecom"] = telecom

    # Add address if available
    if patient.address_line1 or patient.city:
        fhir_patient["address"] = [{
            "use": "home",
            "line": [patient.address_line1, patient.address_line2] if patient.address_line2 else [patient.address_line1],
            "city": patient.city,
            "state": patient.state,
            "postalCode": patient.postal_code,
            "country": patient.country,
        }]

    headers = {"Content-Type": "application/fhir+json"}

    async with httpx.AsyncClient(timeout=30) as client:
        if patient.fhir_id:
            # Update existing
            fhir_patient["id"] = patient.fhir_id
            r = await client.put(
                f"{FHIR_BASE}/Patient/{patient.fhir_id}",
                json=fhir_patient,
                headers=headers
            )
        else:
            # Create new
            r = await client.post(
                f"{FHIR_BASE}/Patient",
                json=fhir_patient,
                headers=headers
            )

        if r.status_code in (200, 201):
            return r.json().get("id")
        else:
            # Log error but don't fail
            print(f"FHIR sync error: {r.status_code} - {r.text}")
            return None


def sync_patient_to_fhir_sync(patient: Patient) -> str:
    """Synchronous version of FHIR sync for use in sync views."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(sync_patient_to_fhir(patient))


class PatientListView(APIView):
    """List all patients or create a new patient."""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        """List patients with optional filtering."""
        queryset = Patient.objects.all()

        # Search by name or MRN
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(mrn__icontains=search)
            )

        # Filter by status
        patient_status = request.query_params.get("status")
        if patient_status:
            queryset = queryset.filter(status=patient_status)

        # Pagination
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))
        total = queryset.count()
        queryset = queryset[offset:offset + limit]

        serializer = PatientListSerializer(queryset, many=True)
        return Response({
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": serializer.data
        })

    def post(self, request):
        """Create a new patient."""
        serializer = PatientDetailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Generate MRN if not provided
        if not serializer.validated_data.get("mrn"):
            serializer.validated_data["mrn"] = generate_mrn()

        patient = serializer.save()

        # Sync to FHIR
        try:
            fhir_id = sync_patient_to_fhir_sync(patient)
            if fhir_id:
                patient.fhir_id = fhir_id
                patient.save(update_fields=["fhir_id"])
        except Exception as e:
            print(f"FHIR sync failed: {e}")

        return Response(
            PatientDetailSerializer(patient).data,
            status=status.HTTP_201_CREATED
        )


# Need to import models for Q objects
from django.db import models


class PatientDetailView(APIView):
    """Retrieve, update or delete a patient."""
    authentication_classes = []
    permission_classes = []

    def get(self, request, patient_id):
        """Get patient details."""
        patient = get_object_or_404(Patient, id=patient_id)
        serializer = PatientDetailSerializer(patient)
        return Response(serializer.data)

    def put(self, request, patient_id):
        """Update patient."""
        patient = get_object_or_404(Patient, id=patient_id)
        serializer = PatientDetailSerializer(patient, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        patient = serializer.save()

        # Sync to FHIR
        try:
            fhir_id = sync_patient_to_fhir_sync(patient)
            if fhir_id and not patient.fhir_id:
                patient.fhir_id = fhir_id
                patient.save(update_fields=["fhir_id"])
        except Exception as e:
            print(f"FHIR sync failed: {e}")

        return Response(PatientDetailSerializer(patient).data)

    def delete(self, request, patient_id):
        """Delete patient (soft delete by setting status to inactive)."""
        patient = get_object_or_404(Patient, id=patient_id)
        patient.status = "inactive"
        patient.save(update_fields=["status"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class PatientImportView(APIView):
    """Import patients from JSON."""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        """Import multiple patients from JSON."""
        serializer = PatientImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        patients_data = serializer.validated_data["patients"]
        created = []
        errors = []

        with transaction.atomic():
            for i, patient_data in enumerate(patients_data):
                try:
                    # Generate MRN if not provided
                    if not patient_data.get("mrn"):
                        patient_data["mrn"] = generate_mrn()

                    # Check for duplicate MRN
                    if Patient.objects.filter(mrn=patient_data["mrn"]).exists():
                        errors.append({
                            "index": i,
                            "mrn": patient_data.get("mrn"),
                            "error": "Patient with this MRN already exists"
                        })
                        continue

                    patient_serializer = PatientDetailSerializer(data=patient_data)
                    if patient_serializer.is_valid():
                        patient = patient_serializer.save()

                        # Sync to FHIR
                        try:
                            fhir_id = sync_patient_to_fhir_sync(patient)
                            if fhir_id:
                                patient.fhir_id = fhir_id
                                patient.save(update_fields=["fhir_id"])
                        except Exception as e:
                            print(f"FHIR sync failed for patient {patient.mrn}: {e}")

                        created.append({
                            "id": patient.id,
                            "mrn": patient.mrn,
                            "name": patient.full_name,
                            "fhir_id": patient.fhir_id
                        })
                    else:
                        errors.append({
                            "index": i,
                            "data": patient_data,
                            "errors": patient_serializer.errors
                        })
                except Exception as e:
                    errors.append({
                        "index": i,
                        "error": str(e)
                    })

        return Response({
            "imported": len(created),
            "failed": len(errors),
            "created": created,
            "errors": errors
        }, status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST)


class PatientDocumentListView(APIView):
    """List or upload documents for a patient."""
    authentication_classes = []
    permission_classes = []

    def get(self, request, patient_id):
        """List all documents for a patient."""
        patient = get_object_or_404(Patient, id=patient_id)
        documents = patient.documents.all()

        # Filter by type
        doc_type = request.query_params.get("type")
        if doc_type:
            documents = documents.filter(document_type=doc_type)

        serializer = PatientDocumentSerializer(documents, many=True)
        return Response(serializer.data)

    def post(self, request, patient_id):
        """Upload a document for a patient."""
        patient = get_object_or_404(Patient, id=patient_id)

        serializer = PatientDocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        document = serializer.save(patient=patient)
        return Response(
            PatientDocumentSerializer(document).data,
            status=status.HTTP_201_CREATED
        )


class PatientByMRNView(APIView):
    """Get patient by MRN."""
    authentication_classes = []
    permission_classes = []

    def get(self, request, mrn):
        patient = get_object_or_404(Patient, mrn=mrn)
        serializer = PatientDetailSerializer(patient)
        return Response(serializer.data)


class PatientByFHIRView(APIView):
    """Get patient by FHIR ID."""
    authentication_classes = []
    permission_classes = []

    def get(self, request, fhir_id):
        patient = get_object_or_404(Patient, fhir_id=fhir_id)
        serializer = PatientDetailSerializer(patient)
        return Response(serializer.data)
