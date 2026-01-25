# Generated migration for users app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('username', models.CharField(blank=True, max_length=150)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('role', models.CharField(choices=[('admin', 'Administrator'), ('doctor', 'Doctor/Physician'), ('nurse', 'Nurse'), ('technician', 'Lab Technician'), ('receptionist', 'Receptionist'), ('viewer', 'Read-Only Viewer')], default='viewer', max_length=20)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('department', models.CharField(blank=True, choices=[('general', 'General Medicine'), ('cardiology', 'Cardiology'), ('neurology', 'Neurology'), ('pediatrics', 'Pediatrics'), ('oncology', 'Oncology'), ('emergency', 'Emergency'), ('icu', 'Intensive Care Unit'), ('surgery', 'Surgery'), ('radiology', 'Radiology'), ('laboratory', 'Laboratory'), ('pharmacy', 'Pharmacy'), ('other', 'Other')], max_length=50)),
                ('title', models.CharField(blank=True, help_text='Professional title (e.g., MD, RN)', max_length=100)),
                ('license_number', models.CharField(blank=True, help_text='Medical license number', max_length=50)),
                ('specialty', models.CharField(blank=True, max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('last_login_ip', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to.', related_name='custom_user_set', related_query_name='custom_user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='custom_user_set', related_query_name='custom_user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('login', 'Login'), ('logout', 'Logout'), ('create', 'Create'), ('read', 'Read'), ('update', 'Update'), ('delete', 'Delete'), ('export', 'Export'), ('acknowledge', 'Acknowledge Alert'), ('other', 'Other')], max_length=20)),
                ('resource_type', models.CharField(help_text='Type of resource (e.g., Patient, Device)', max_length=50)),
                ('resource_id', models.CharField(blank=True, help_text='ID of the affected resource', max_length=100)),
                ('description', models.TextField(blank=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=500)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user', 'timestamp'], name='users_audit_user_id_77a88f_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['action', 'timestamp'], name='users_audit_action_b8d3e1_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['resource_type', 'resource_id'], name='users_audit_resourc_a2e5a3_idx'),
        ),
    ]
