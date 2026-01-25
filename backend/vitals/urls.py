from django.urls import path
from .views import VitalsEventView
from .api_internal import VitalsEventInternalView

urlpatterns = [
    path("events", VitalsEventView.as_view()),
    path("internal/events/<int:event_id>", VitalsEventInternalView.as_view()),
]

