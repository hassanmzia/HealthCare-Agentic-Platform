from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Recommendation

class RecommendationsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        patient_id = request.query_params.get("patient_id")
        qs = Recommendation.objects.all().order_by("-created_at")[:50]
        if patient_id:
            qs = qs.filter(patient_id=patient_id).order_by("-created_at")[:50]

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

