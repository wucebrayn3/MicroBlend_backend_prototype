import json
import time

from django.http import StreamingHttpResponse
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.realtime.serializers import RealtimeEventSerializer
from apps.realtime.services import get_user_event_queryset


class RealtimeEventListView(generics.ListAPIView):
    serializer_class = RealtimeEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        after_id = int(self.request.query_params.get("after_id", 0))
        return get_user_event_queryset(self.request.user, after_id=after_id).order_by("id")


class RealtimeStreamView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        after_id = int(request.query_params.get("after_id", 0))
        timeout_seconds = int(request.query_params.get("timeout", 30))
        started_at = time.time()

        def event_stream():
            cursor = after_id
            while time.time() - started_at < timeout_seconds:
                events = get_user_event_queryset(request.user, after_id=cursor).order_by("id")[:100]
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
