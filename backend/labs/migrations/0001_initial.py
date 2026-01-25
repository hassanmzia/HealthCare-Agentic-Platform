# Generated migration for labs app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('patients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LabTestCatalog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='LOINC or local code', max_length=50, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('category', models.CharField(choices=[('chemistry', 'Chemistry'), ('hematology', 'Hematology'), ('urinalysis', 'Urinalysis'), ('microbiology', 'Microbiology'), ('immunology', 'Immunology'), ('coagulation', 'Coagulation'), ('endocrine', 'Endocrine'), ('cardiac', 'Cardiac Markers'), ('toxicology', 'Toxicology'), ('genetic', 'Genetic Testing'), ('other', 'Other')], max_length=50)),
                ('specimen_type', models.CharField(choices=[('blood', 'Blood'), ('serum', 'Serum'), ('plasma', 'Plasma'), ('urine', 'Urine'), ('stool', 'Stool'), ('csf', 'Cerebrospinal Fluid'), ('swab', 'Swab'), ('tissue', 'Tissue'), ('other', 'Other')], max_length=50)),
                ('unit', models.CharField(blank=True, help_text='Unit of measurement', max_length=50)),
                ('reference_range_low', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('reference_range_high', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('reference_range_text', models.CharField(blank=True, help_text='Text description of normal range', max_length=100)),
                ('critical_low', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('critical_high', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('typical_tat_hours', models.IntegerField(default=24, help_text='Typical turnaround time in hours')),
                ('is_active', models.BooleanField(default=True)),
                ('requires_fasting', models.BooleanField(default=False)),
                ('special_instructions', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Lab Test',
                'verbose_name_plural': 'Lab Test Catalog',
                'ordering': ['category', 'name'],
            },
        ),
        migrations.CreateModel(
            name='LabPanel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tests', models.ManyToManyField(related_name='panels', to='labs.labtestcatalog')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='LabOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_number', models.CharField(max_length=50, unique=True)),
                ('fhir_id', models.CharField(blank=True, help_text='FHIR ServiceRequest ID', max_length=100)),
                ('encounter_id', models.IntegerField(blank=True, help_text='Associated encounter ID', null=True)),
                ('status', models.CharField(choices=[('ordered', 'Ordered'), ('collected', 'Specimen Collected'), ('received', 'Received by Lab'), ('processing', 'Processing'), ('partial', 'Partial Results'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='ordered', max_length=20)),
                ('priority', models.CharField(choices=[('routine', 'Routine'), ('urgent', 'Urgent'), ('stat', 'STAT')], default='routine', max_length=20)),
                ('ordering_physician', models.CharField(max_length=200)),
                ('ordering_physician_id', models.CharField(blank=True, max_length=100)),
                ('clinical_notes', models.TextField(blank=True, help_text='Clinical indication/reason')),
                ('diagnosis_codes', models.JSONField(blank=True, default=list, help_text='ICD-10 codes')),
                ('specimen_collected_at', models.DateTimeField(blank=True, null=True)),
                ('specimen_collector', models.CharField(blank=True, max_length=200)),
                ('specimen_id', models.CharField(blank=True, max_length=100)),
                ('received_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('ordered_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('cancelled_by', models.CharField(blank=True, max_length=200)),
                ('cancellation_reason', models.TextField(blank=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lab_orders', to='patients.patient')),
            ],
            options={
                'verbose_name': 'Lab Order',
                'verbose_name_plural': 'Lab Orders',
                'ordering': ['-ordered_at'],
            },
        ),
        migrations.CreateModel(
            name='LabOrderTest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tests', to='labs.laborder')),
                ('test', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='order_items', to='labs.labtestcatalog')),
            ],
            options={
                'ordering': ['test__category', 'test__name'],
                'unique_together': {('order', 'test')},
            },
        ),
        migrations.CreateModel(
            name='LabResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fhir_id', models.CharField(blank=True, help_text='FHIR Observation ID', max_length=100)),
                ('value_numeric', models.DecimalField(blank=True, decimal_places=5, max_digits=15, null=True)),
                ('value_text', models.CharField(blank=True, help_text='Text result or qualitative value', max_length=500)),
                ('unit', models.CharField(blank=True, max_length=50)),
                ('reference_range_low', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('reference_range_high', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('reference_range_text', models.CharField(blank=True, max_length=100)),
                ('flag', models.CharField(choices=[('N', 'Normal'), ('L', 'Low'), ('H', 'High'), ('LL', 'Critical Low'), ('HH', 'Critical High'), ('A', 'Abnormal'), ('U', 'Undetermined')], default='N', max_length=5)),
                ('is_critical', models.BooleanField(default=False)),
                ('interpretation', models.TextField(blank=True)),
                ('performed_by', models.CharField(blank=True, max_length=200)),
                ('verified_by', models.CharField(blank=True, max_length=200)),
                ('performed_at', models.DateTimeField(blank=True, null=True)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('comments', models.TextField(blank=True)),
                ('method', models.CharField(blank=True, help_text='Testing method/instrument', max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order_test', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='result', to='labs.labordertest')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='laborder',
            index=models.Index(fields=['patient', 'status'], name='labs_labord_patient_a3e8f2_idx'),
        ),
        migrations.AddIndex(
            model_name='laborder',
            index=models.Index(fields=['order_number'], name='labs_labord_order_n_e51a2c_idx'),
        ),
        migrations.AddIndex(
            model_name='laborder',
            index=models.Index(fields=['status', 'ordered_at'], name='labs_labord_status_7d8c1a_idx'),
        ),
    ]
