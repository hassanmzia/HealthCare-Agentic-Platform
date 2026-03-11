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
    feature_importance = models.JSONField(
        default=list,
        help_text="Feature attribution: [{feature, value, direction}, ...]",
    )
    source_guideline = models.CharField(
        max_length=255, blank=True, default="",
        help_text="Clinical guideline that supports this recommendation",
    )
    evidence_level = models.CharField(
        max_length=5, blank=True, default="",
        help_text="Evidence grade: A/B/C/D/E",
    )
    agent_name = models.CharField(
        max_length=100, blank=True, default="",
        help_text="Name of the agent that generated this recommendation",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.severity}) - {self.patient_id}"


class AgentModelCard(models.Model):
    """Model card for agent transparency and regulatory compliance."""
    agent_name = models.CharField(max_length=100, unique=True)
    agent_id = models.IntegerField()
    version = models.CharField(max_length=20)
    agent_tier = models.CharField(max_length=50)
    description = models.TextField()
    intended_use = models.TextField()
    out_of_scope_uses = models.JSONField(default=list)
    model_type = models.CharField(max_length=50)
    underlying_models = models.JSONField(default=list)
    safety_considerations = models.JSONField(default=list)
    known_limitations = models.JSONField(default=list)
    failure_modes = models.JSONField(default=list)
    hitl_requirements = models.TextField(blank=True, default="")
    clinical_evidence_level = models.CharField(max_length=5, blank=True, default="")
    source_guidelines = models.JSONField(default=list)
    performance_metrics = models.JSONField(
        default=dict,
        help_text="Latest performance: {precision, recall, f1, auc_roc, ...}",
    )
    fairness_analyses = models.JSONField(
        default=list,
        help_text="Fairness results: [{group_by, disparity_ratio, assessment, subgroups}]",
    )
    monitoring_metrics = models.JSONField(default=list)
    alerting_thresholds = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["agent_id"]

    def __str__(self):
        return f"{self.agent_name} v{self.version}"


class AgentDecisionLog(models.Model):
    """Audit log for agent decisions with rationale and feature attribution."""
    DECISION_TYPES = [
        ("risk_assessment", "Risk Assessment"),
        ("recommendation", "Recommendation"),
        ("intervention", "Intervention"),
        ("alert", "Alert"),
        ("hitl_request", "HITL Request"),
    ]

    trace_id = models.CharField(max_length=100, db_index=True)
    agent_name = models.CharField(max_length=100, db_index=True)
    agent_tier = models.CharField(max_length=50, blank=True, default="")
    patient_id = models.CharField(max_length=100, db_index=True)
    decision_type = models.CharField(max_length=30, choices=DECISION_TYPES, default="recommendation")
    decision = models.TextField()
    rationale = models.TextField()
    confidence = models.FloatField(default=0.0)
    feature_contributions = models.JSONField(
        default=list,
        help_text="[{feature, value, contribution, direction}, ...]",
    )
    alternatives = models.JSONField(
        default=list,
        help_text="Alternative decisions considered",
    )
    evidence_references = models.JSONField(
        default=list,
        help_text="Clinical evidence supporting the decision",
    )
    input_summary = models.JSONField(default=dict)
    output_summary = models.JSONField(default=dict)
    requires_hitl = models.BooleanField(default=False)
    safety_flags = models.JSONField(default=list)
    duration_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["trace_id", "created_at"]),
            models.Index(fields=["patient_id", "created_at"]),
        ]

    def __str__(self):
        return f"{self.agent_name}: {self.decision[:50]}"
