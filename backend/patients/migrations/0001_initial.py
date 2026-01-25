# Generated migration for patients app

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mrn', models.CharField(max_length=50, unique=True, verbose_name='Medical Record Number')),
                ('fhir_id', models.CharField(blank=True, help_text='FHIR Patient resource ID', max_length=100, null=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('middle_name', models.CharField(blank=True, max_length=100)),
                ('prefix', models.CharField(blank=True, help_text='e.g., Mr., Mrs., Dr.', max_length=20)),
                ('suffix', models.CharField(blank=True, help_text='e.g., Jr., Sr., III', max_length=20)),
                ('date_of_birth', models.DateField()),
                ('gender', models.CharField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('unknown', 'Unknown')], default='unknown', max_length=10)),
                ('blood_type', models.CharField(choices=[('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'), ('unknown', 'Unknown')], default='unknown', max_length=10)),
                ('ssn', models.CharField(blank=True, help_text='XXX-XX-XXXX', max_length=11, verbose_name='SSN')),
                ('phone', models.CharField(blank=True, max_length=17, validators=[django.core.validators.RegexValidator(message="Phone number format: '+999999999'", regex='^\\+?1?\\d{9,15}$')])),
                ('phone_secondary', models.CharField(blank=True, max_length=17, validators=[django.core.validators.RegexValidator(message="Phone number format: '+999999999'", regex='^\\+?1?\\d{9,15}$')])),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('address_line1', models.CharField(blank=True, max_length=255)),
                ('address_line2', models.CharField(blank=True, max_length=255)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('state', models.CharField(blank=True, max_length=100)),
                ('postal_code', models.CharField(blank=True, max_length=20)),
                ('country', models.CharField(default='USA', max_length=100)),
                ('emergency_contact_name', models.CharField(blank=True, max_length=200)),
                ('emergency_contact_phone', models.CharField(blank=True, max_length=17)),
                ('emergency_contact_relationship', models.CharField(blank=True, max_length=50)),
                ('insurance_provider', models.CharField(blank=True, max_length=200)),
                ('insurance_policy_number', models.CharField(blank=True, max_length=100)),
                ('insurance_group_number', models.CharField(blank=True, max_length=100)),
                ('allergies', models.JSONField(blank=True, default=list, help_text='List of allergies')),
                ('medications', models.JSONField(blank=True, default=list, help_text='Current medications')),
                ('medical_conditions', models.JSONField(blank=True, default=list, help_text='Chronic conditions')),
                ('medical_history', models.TextField(blank=True, help_text='Additional medical history notes')),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('deceased', 'Deceased')], default='active', max_length=20)),
                ('primary_care_physician', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Patient',
                'verbose_name_plural': 'Patients',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PatientDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_type', models.CharField(choices=[('xray', 'X-Ray'), ('ct_scan', 'CT Scan'), ('mri', 'MRI'), ('lab_report', 'Lab Report'), ('pathology', 'Pathology Report'), ('prescription', 'Prescription'), ('referral', 'Referral'), ('consent', 'Consent Form'), ('other', 'Other')], max_length=50)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('file_url', models.URLField(blank=True, help_text='URL to the document/image')),
                ('file_data', models.TextField(blank=True, help_text='Base64 encoded file data for small files')),
                ('mime_type', models.CharField(blank=True, max_length=100)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('uploaded_by', models.CharField(blank=True, max_length=200)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='patients.patient')),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
    ]
