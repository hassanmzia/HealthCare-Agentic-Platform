# Generated migration for alerts app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('patients', '0001_initial'),
        ('devices', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlertRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('vital_type', models.CharField(choices=[('heart_rate', 'Heart Rate'), ('blood_pressure_systolic', 'Blood Pressure (Systolic)'), ('blood_pressure_diastolic', 'Blood Pressure (Diastolic)'), ('oxygen_saturation', 'Oxygen Saturation (SpO2)'), ('temperature', 'Temperature'), ('respiratory_rate', 'Respiratory Rate'), ('glucose', 'Blood Glucose')], max_length=50)),
                ('condition', models.CharField(choices=[('gt', 'Greater Than'), ('gte', 'Greater Than or Equal'), ('lt', 'Less Than'), ('lte', 'Less Than or Equal'), ('eq', 'Equal To'), ('range_outside', 'Outside Range')], default='gt', max_length=20)),
                ('threshold_value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('threshold_value_high', models.DecimalField(blank=True, decimal_places=2, help_text='Upper bound for range_outside condition', max_digits=10, null=True)),
                ('severity', models.CharField(choices=[('info', 'Information'), ('warning', 'Warning'), ('critical', 'Critical')], default='warning', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('cooldown_minutes', models.IntegerField(default=15, help_text='Minutes before re-alerting for same condition')),
                ('auto_acknowledge_minutes', models.IntegerField(default=0, help_text='Auto-acknowledge after N minutes (0=never)')),
                ('notify_on_trigger', models.BooleanField(default=True)),
                ('escalate_after_minutes', models.IntegerField(default=30, help_text='Escalate if not acknowledged (0=never)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.CharField(blank=True, max_length=200)),
                ('patient', models.ForeignKey(blank=True, help_text='Leave blank for global rule', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='alert_rules', to='patients.patient')),
            ],
            options={
                'verbose_name': 'Alert Rule',
                'verbose_name_plural': 'Alert Rules',
                'ordering': ['-severity', 'vital_type', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vital_type', models.CharField(max_length=50)),
                ('vital_value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('threshold_value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('condition', models.CharField(max_length=20)),
                ('severity', models.CharField(choices=[('info', 'Information'), ('warning', 'Warning'), ('critical', 'Critical')], default='warning', max_length=20)),
                ('status', models.CharField(choices=[('active', 'Active'), ('acknowledged', 'Acknowledged'), ('resolved', 'Resolved'), ('escalated', 'Escalated'), ('auto_resolved', 'Auto-Resolved')], default='active', max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('triggered_at', models.DateTimeField(auto_now_add=True)),
                ('acknowledged_at', models.DateTimeField(blank=True, null=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('escalated_at', models.DateTimeField(blank=True, null=True)),
                ('acknowledged_by', models.CharField(blank=True, max_length=200)),
                ('resolved_by', models.CharField(blank=True, max_length=200)),
                ('resolution_notes', models.TextField(blank=True)),
                ('fhir_observation_id', models.CharField(blank=True, max_length=100)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alerts', to='patients.patient')),
                ('device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='alerts', to='devices.device')),
                ('rule', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='alerts', to='alerts.alertrule')),
            ],
            options={
                'verbose_name': 'Alert',
                'verbose_name_plural': 'Alerts',
                'ordering': ['-triggered_at'],
            },
        ),
        migrations.CreateModel(
            name='AlertNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('dashboard', 'Dashboard'), ('email', 'Email'), ('sms', 'SMS'), ('push', 'Push Notification'), ('escalation', 'Escalation')], max_length=20)),
                ('recipient', models.CharField(blank=True, help_text='Email, phone, or user ID', max_length=200)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed'), ('read', 'Read')], default='pending', max_length=20)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True)),
                ('alert', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='alerts.alert')),
            ],
            options={
                'ordering': ['-sent_at'],
            },
        ),
        migrations.AddIndex(
            model_name='alert',
            index=models.Index(fields=['patient', 'status'], name='alerts_aler_patient_5a2f25_idx'),
        ),
        migrations.AddIndex(
            model_name='alert',
            index=models.Index(fields=['status', 'severity'], name='alerts_aler_status_b8d7cd_idx'),
        ),
        migrations.AddIndex(
            model_name='alert',
            index=models.Index(fields=['triggered_at'], name='alerts_aler_trigger_4c0c06_idx'),
        ),
    ]
