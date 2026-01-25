from django.urls import path
from django.http import JsonResponse
from .views import VitalsEventView, VitalsEventInternalView

def index(_request):
    return JsonResponse({
        "service": "vitals",
        "status": "ok",
        "endpoints": {
            "POST /api/v1/vitals/events": "ingest device vitals",
            "GET  /api/v1/vitals/internal/events/<id>": "fetch stored vitals event"
        }
    })

urlpatterns = [
    path("", index),
    path("events", VitalsEventView.as_view()),
    path("internal/events/<int:event_id>", VitalsEventInternalView.as_view()),
]

