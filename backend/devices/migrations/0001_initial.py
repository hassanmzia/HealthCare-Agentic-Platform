# Generated migration for devices app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('patients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_id', models.CharField(help_text='Unique device identifier', max_length=100, unique=True)),
                ('fhir_id', models.CharField(blank=True, help_text='FHIR Device resource ID', max_length=100, null=True)),
                ('serial_number', models.CharField(blank=True, max_length=100)),
                ('name', models.CharField(max_length=200)),
                ('device_type', models.CharField(choices=[('vital_monitor', 'Vital Signs Monitor'), ('pulse_oximeter', 'Pulse Oximeter'), ('bp_monitor', 'Blood Pressure Monitor'), ('thermometer', 'Thermometer'), ('ecg_monitor', 'ECG Monitor'), ('glucose_monitor', 'Glucose Monitor'), ('weight_scale', 'Weight Scale'), ('multi_parameter', 'Multi-Parameter Monitor'), ('wearable', 'Wearable Device'), ('other', 'Other')], default='vital_monitor', max_length=50)),
                ('manufacturer', models.CharField(blank=True, max_length=200)),
                ('model_number', models.CharField(blank=True, max_length=100)),
                ('firmware_version', models.CharField(blank=True, max_length=50)),
                ('facility', models.CharField(blank=True, help_text='Hospital/Clinic name', max_length=200)),
                ('department', models.CharField(blank=True, max_length=200)),
                ('room', models.CharField(blank=True, max_length=50)),
                ('bed', models.CharField(blank=True, max_length=50)),
                ('capabilities', models.JSONField(blank=True, default=list, help_text='List of vital signs this device can measure')),
                ('reading_interval_seconds', models.IntegerField(default=60, help_text='How often device sends readings')),
                ('config', models.JSONField(blank=True, default=dict, help_text='Device-specific configuration')),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('maintenance', 'Under Maintenance'), ('retired', 'Retired')], default='active', max_length=20)),
                ('last_seen', models.DateTimeField(blank=True, help_text='Last time device sent data', null=True)),
                ('battery_level', models.IntegerField(blank=True, help_text='Battery percentage 0-100', null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Device',
                'verbose_name_plural': 'Devices',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DeviceAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('unassigned_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('assigned_by', models.CharField(blank=True, help_text='Staff member who made assignment', max_length=200)),
                ('reason', models.TextField(blank=True, help_text='Reason for assignment')),
                ('notes', models.TextField(blank=True)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='devices.device')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='device_assignments', to='patients.patient')),
            ],
            options={
                'verbose_name': 'Device Assignment',
                'verbose_name_plural': 'Device Assignments',
                'ordering': ['-assigned_at'],
            },
        ),
    ]
