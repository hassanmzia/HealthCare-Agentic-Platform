from django.db import models

class GuidelineChunk(models.Model):
    doc_id = models.CharField(max_length=200)
    chunk_id = models.CharField(max_length=200)
    text = models.TextField()
    embedding = models.BinaryField(null=True, blank=True)  # placeholder for now
    created_at = models.DateTimeField(auto_now_add=True)

