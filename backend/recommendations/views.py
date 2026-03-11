from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg, Count, Q
from .models import Recommendation, AgentModelCard, AgentDecisionLog


class RecommendationsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        patient_id = request.query_params.get("patient_id")
        qs = Recommendation.objects.all()
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        qs = qs.order_by("-created_at")[:50]

        return Response([
            {
                "id": r.id,
                "patient_id": r.patient_id,
                "created_at": r.created_at.isoformat(),
                "severity": r.severity,
                "title": r.title,
                "summary": r.summary,
                "rationale": r.rationale,
                "evidence": r.evidence or [],
                "confidence": r.confidence,
                "feature_importance": r.feature_importance or [],
                "evidence_level": r.evidence_level,
                "source_guideline": r.source_guideline,
                "agent_name": r.agent_name,
            }
            for r in qs
        ])

    def post(self, request):
        data = request.data
        recommendation = Recommendation.objects.create(
            patient_id=data.get("patient_id", ""),
            severity=data.get("severity", "info"),
            title=data.get("title", "Recommendation"),
            summary=data.get("summary", ""),
            actions=data.get("actions", []),
            rationale=data.get("rationale", ""),
            evidence=data.get("evidence", []),
            confidence=data.get("confidence", 0.0),
            feature_importance=data.get("feature_importance", []),
            source_guideline=data.get("source_guideline", ""),
            evidence_level=data.get("evidence_level", ""),
            agent_name=data.get("agent_name", ""),
        )
        return Response(
            {
                "id": recommendation.id,
                "patient_id": recommendation.patient_id,
                "created_at": recommendation.created_at.isoformat(),
                "severity": recommendation.severity,
                "title": recommendation.title,
                "summary": recommendation.summary,
                "rationale": recommendation.rationale,
                "evidence": recommendation.evidence or [],
                "confidence": recommendation.confidence,
                "feature_importance": recommendation.feature_importance or [],
            },
            status=status.HTTP_201_CREATED,
        )


class RecommendationExplainView(APIView):
    """Explain a specific recommendation with feature attribution."""
    authentication_classes = []
    permission_classes = []

    def get(self, request, pk):
        try:
            rec = Recommendation.objects.get(pk=pk)
        except Recommendation.DoesNotExist:
            return Response(
                {"error": "Recommendation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Build explanation
        contributions = rec.feature_importance or []
        top_drivers = [
            c["feature"] for c in sorted(
                contributions,
                key=lambda x: abs(x.get("value", 0)),
                reverse=True,
            )[:3]
        ]

        explanation = {
            "recommendation_id": rec.id,
            "title": rec.title,
            "severity": rec.severity,
            "confidence": rec.confidence,
            "rationale": rec.rationale,
            "evidence_level": rec.evidence_level,
            "source_guideline": rec.source_guideline,
            "agent_name": rec.agent_name,
            "feature_attribution": {
                "contributions": contributions,
                "top_drivers": top_drivers,
            },
            "evidence": rec.evidence or [],
            "natural_language_explanation": _build_explanation(rec, top_drivers),
        }

        return Response(explanation)


class AgentModelCardView(APIView):
    """CRUD for agent model cards."""
    authentication_classes = []
    permission_classes = []

    def get(self, request, agent_name=None):
        if agent_name:
            try:
                card = AgentModelCard.objects.get(agent_name=agent_name)
            except AgentModelCard.DoesNotExist:
                return Response(
                    {"error": "Model card not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(_serialize_model_card(card))

        cards = AgentModelCard.objects.all()
        return Response([_serialize_model_card(c) for c in cards])

    def post(self, request):
        data = request.data
        card, created = AgentModelCard.objects.update_or_create(
            agent_name=data.get("agent_name", ""),
            defaults={
                "agent_id": data.get("agent_id", 0),
                "version": data.get("version", "1.0.0"),
                "agent_tier": data.get("agent_tier", ""),
                "description": data.get("description", ""),
                "intended_use": data.get("intended_use", ""),
                "out_of_scope_uses": data.get("out_of_scope_uses", []),
                "model_type": data.get("model_type", ""),
                "underlying_models": data.get("underlying_models", []),
                "safety_considerations": data.get("safety_considerations", []),
                "known_limitations": data.get("known_limitations", []),
                "failure_modes": data.get("failure_modes", []),
                "hitl_requirements": data.get("hitl_requirements", ""),
                "clinical_evidence_level": data.get("clinical_evidence_level", ""),
                "source_guidelines": data.get("source_guidelines", []),
                "performance_metrics": data.get("performance_metrics", {}),
                "fairness_analyses": data.get("fairness_analyses", []),
                "monitoring_metrics": data.get("monitoring_metrics", []),
                "alerting_thresholds": data.get("alerting_thresholds", {}),
            },
        )
        return Response(
            _serialize_model_card(card),
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class AgentDecisionLogView(APIView):
    """Query agent decision audit logs."""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        qs = AgentDecisionLog.objects.all()

        # Filters
        trace_id = request.query_params.get("trace_id")
        patient_id = request.query_params.get("patient_id")
        agent_name = request.query_params.get("agent_name")
        decision_type = request.query_params.get("decision_type")
        requires_hitl = request.query_params.get("requires_hitl")

        if trace_id:
            qs = qs.filter(trace_id=trace_id)
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if agent_name:
            qs = qs.filter(agent_name=agent_name)
        if decision_type:
            qs = qs.filter(decision_type=decision_type)
        if requires_hitl is not None:
            qs = qs.filter(requires_hitl=requires_hitl.lower() == "true")

        limit = min(int(request.query_params.get("limit", 50)), 200)
        qs = qs[:limit]

        return Response([
            {
                "id": d.id,
                "trace_id": d.trace_id,
                "agent_name": d.agent_name,
                "agent_tier": d.agent_tier,
                "patient_id": d.patient_id,
                "decision_type": d.decision_type,
                "decision": d.decision,
                "rationale": d.rationale,
                "confidence": d.confidence,
                "feature_contributions": d.feature_contributions,
                "alternatives": d.alternatives,
                "evidence_references": d.evidence_references,
                "requires_hitl": d.requires_hitl,
                "safety_flags": d.safety_flags,
                "duration_ms": d.duration_ms,
                "created_at": d.created_at.isoformat(),
            }
            for d in qs
        ])

    def post(self, request):
        data = request.data
        log = AgentDecisionLog.objects.create(
            trace_id=data.get("trace_id", ""),
            agent_name=data.get("agent_name", ""),
            agent_tier=data.get("agent_tier", ""),
            patient_id=data.get("patient_id", ""),
            decision_type=data.get("decision_type", "recommendation"),
            decision=data.get("decision", ""),
            rationale=data.get("rationale", ""),
            confidence=data.get("confidence", 0.0),
            feature_contributions=data.get("feature_contributions", []),
            alternatives=data.get("alternatives", []),
            evidence_references=data.get("evidence_references", []),
            input_summary=data.get("input_summary", {}),
            output_summary=data.get("output_summary", {}),
            requires_hitl=data.get("requires_hitl", False),
            safety_flags=data.get("safety_flags", []),
            duration_ms=data.get("duration_ms", 0),
        )
        return Response({"id": log.id, "created_at": log.created_at.isoformat()}, status=status.HTTP_201_CREATED)


class AgentDecisionStatsView(APIView):
    """Aggregate decision statistics for observability dashboards."""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        qs = AgentDecisionLog.objects.all()

        patient_id = request.query_params.get("patient_id")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)

        total = qs.count()
        if total == 0:
            return Response({"total": 0, "agents": [], "hitl_rate": 0})

        by_agent = (
            qs.values("agent_name")
            .annotate(
                count=Count("id"),
                avg_confidence=Avg("confidence"),
                avg_duration_ms=Avg("duration_ms"),
                hitl_count=Count("id", filter=Q(requires_hitl=True)),
            )
            .order_by("-count")
        )

        by_type = (
            qs.values("decision_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        hitl_total = qs.filter(requires_hitl=True).count()

        return Response({
            "total": total,
            "hitl_rate": round(hitl_total / total, 4) if total else 0,
            "by_agent": list(by_agent),
            "by_type": list(by_type),
            "avg_confidence": round(
                qs.aggregate(avg=Avg("confidence"))["avg"] or 0, 4
            ),
            "avg_duration_ms": round(
                qs.aggregate(avg=Avg("duration_ms"))["avg"] or 0, 1
            ),
        })


# ── Helpers ──────────────────────────────────────────────────────────


def _build_explanation(rec, top_drivers):
    parts = [f"Recommendation '{rec.title}' was generated"]
    if rec.agent_name:
        parts[0] += f" by {rec.agent_name}"
    parts[0] += "."

    if top_drivers:
        driver_strs = []
        for fi in rec.feature_importance or []:
            if fi.get("feature") in top_drivers:
                driver_strs.append(
                    f"{fi['feature']} (importance: {fi.get('value', 0):.2f})"
                )
        if driver_strs:
            parts.append(f"Key factors: {', '.join(driver_strs)}.")

    if rec.evidence_level:
        parts.append(f"Based on {rec.evidence_level}-level evidence.")
    if rec.source_guideline:
        parts.append(f"Source: {rec.source_guideline}.")
    if rec.confidence:
        parts.append(f"Confidence: {rec.confidence:.0%}.")

    return " ".join(parts)


def _serialize_model_card(card):
    return {
        "identity": {
            "agent_name": card.agent_name,
            "agent_id": card.agent_id,
            "version": card.version,
            "agent_tier": card.agent_tier,
            "last_updated": card.updated_at.isoformat(),
        },
        "overview": {
            "description": card.description,
            "intended_use": card.intended_use,
            "out_of_scope_uses": card.out_of_scope_uses,
        },
        "technical": {
            "model_type": card.model_type,
            "underlying_models": card.underlying_models,
        },
        "safety": {
            "considerations": card.safety_considerations,
            "known_limitations": card.known_limitations,
            "failure_modes": card.failure_modes,
            "hitl_requirements": card.hitl_requirements,
        },
        "clinical": {
            "evidence_level": card.clinical_evidence_level,
            "source_guidelines": card.source_guidelines,
        },
        "performance": card.performance_metrics,
        "fairness": card.fairness_analyses,
        "monitoring": {
            "metrics": card.monitoring_metrics,
            "alerting_thresholds": card.alerting_thresholds,
        },
    }
