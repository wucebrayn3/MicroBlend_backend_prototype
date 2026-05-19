import json
import time

from django.http import StreamingHttpResponse
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.realtime.serializers import RealtimeEventSerializer
from apps.realtime.services import get_guest_event_queryset, get_user_event_queryset


class RealtimeEventListView(generics.ListAPIView):
    serializer_class = RealtimeEventSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        after_id = int(self.request.query_params.get("after_id", 0))
        if not self.request.user.is_authenticated:
            guest_key = self.request.query_params.get("guest_key", "")
            return get_guest_event_queryset(guest_key=guest_key, after_id=after_id).order_by("id")
        return get_user_event_queryset(self.request.user, after_id=after_id).order_by("id")


class RealtimeStreamView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        after_id = int(request.query_params.get("after_id", 0))
        timeout_seconds = int(request.query_params.get("timeout", 30))
        started_at = time.time()
        guest_key = request.query_params.get("guest_key", "")

        def event_stream():
            cursor = after_id
            while time.time() - started_at < timeout_seconds:
                if request.user.is_authenticated:
                    events = get_user_event_queryset(request.user, after_id=cursor).order_by("id")[:100]
                else:
                    events = get_guest_event_queryset(guest_key=guest_key, after_id=cursor).order_by("id")[:100]
                if events:
                    for event in events:
                        cursor = event.id
                        payload = RealtimeEventSerializer(event).data
                        yield f"id: {event.id}\n"
                        yield f"event: {event.event_type}\n"
                        yield f"data: {json.dumps(payload)}\n\n"
                time.sleep(1)
            yield "event: keepalive\ndata: {}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
