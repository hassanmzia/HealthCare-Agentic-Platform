from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Recommendation


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
            },
            status=status.HTTP_201_CREATED
        )
