from rest_framework import serializers
from .models import Patient, PatientDocument


class PatientDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientDocument
        fields = [
            "id", "document_type", "title", "description",
            "file_url", "file_data", "mime_type", "metadata",
            "uploaded_at", "uploaded_by"
        ]
        read_only_fields = ["id", "uploaded_at"]


class PatientListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()

    class Meta:
        model = Patient
        fields = [
            "id", "mrn", "fhir_id", "first_name", "last_name",
            "full_name", "date_of_birth", "age", "gender",
            "phone", "email", "status", "created_at"
        ]


class PatientDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail/create/update views."""
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    documents = PatientDocumentSerializer(many=True, read_only=True)

    def to_internal_value(self, data):
        """Convert empty strings to None for non-text fields."""
        # Make a mutable copy
        data = data.copy() if hasattr(data, 'copy') else dict(data)

        # Fields that should convert empty string to None
        nullable_fields = ['date_of_birth', 'ssn', 'phone', 'phone_secondary', 'email']
        for field in nullable_fields:
            if field in data and data[field] == '':
                if field == 'date_of_birth':
                    # date_of_birth is required, so remove empty string to trigger required validation
                    pass
                else:
                    data[field] = None

        return super().to_internal_value(data)

    class Meta:
        model = Patient
        fields = [
            "id", "mrn", "fhir_id",
            # Name
            "first_name", "last_name", "middle_name", "prefix", "suffix", "full_name",
            # Demographics
            "date_of_birth", "age", "gender", "blood_type", "ssn",
            # Contact
            "phone", "phone_secondary", "email",
            # Address
            "address_line1", "address_line2", "city", "state", "postal_code", "country",
            # Emergency Contact
            "emergency_contact_name", "emergency_contact_phone", "emergency_contact_relationship",
            # Insurance
            "insurance_provider", "insurance_policy_number", "insurance_group_number",
            # Medical
            "allergies", "medications", "medical_conditions", "medical_history",
            # Status
            "status", "primary_care_physician",
            # Metadata
            "created_at", "updated_at",
            # Related
            "documents",
        ]
        read_only_fields = ["id", "fhir_id", "created_at", "updated_at"]


class PatientImportSerializer(serializers.Serializer):
    """Serializer for JSON import."""
    patients = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of patient objects to import"
    )

    def validate_patients(self, value):
        errors = []
        for i, patient_data in enumerate(value):
            if not patient_data.get("first_name"):
                errors.append(f"Patient {i+1}: first_name is required")
            if not patient_data.get("last_name"):
                errors.append(f"Patient {i+1}: last_name is required")
            if not patient_data.get("date_of_birth"):
                errors.append(f"Patient {i+1}: date_of_birth is required")
        if errors:
            raise serializers.ValidationError(errors)
        return value
