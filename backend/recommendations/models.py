from django.db import models

class Recommendation(models.Model):
    patient_id = models.CharField(max_length=100)
    severity = models.CharField(max_length=20)
    summary = models.TextField()
    actions = models.JSONField()
    rationale = models.JSONField()
    confidence = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
