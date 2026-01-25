from rest_framework.views import APIView
from rest_framework.response import Response
from .models import VitalsEvent

class VitalsEventInternalView(APIView):
    authentication_classes = []  # add service auth later
    permission_classes = []

    def get(self, request, event_id: int):
        ev = VitalsEvent.objects.get(id=event_id)
        return Response(ev.payload)

