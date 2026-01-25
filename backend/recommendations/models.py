from django.db import models

class Recommendation(models.Model):
    patient_id = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, default="info")
    title = models.CharField(max_length=255, default="Recommendation")
    summary = models.TextField()
    actions = models.JSONField(default=list)
    rationale = models.TextField(default="")
    evidence = models.JSONField(default=list)
    confidence = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
