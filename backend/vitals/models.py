from django.db import models

class VitalsEvent(models.Model):
    device_id = models.CharField(max_length=100)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
