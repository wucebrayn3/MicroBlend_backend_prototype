from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import IsAdmin, IsStaffOrAdmin

from .models import ExternalSystem, SyncEvent
from .serializers import ExternalSystemSerializer, SyncEventAckSerializer, SyncEventSerializer
from .services import mark_sync_event_delivered, mark_sync_event_failed, retry_due_sync_events


class ExternalSystemViewSet(viewsets.ModelViewSet):
    queryset = ExternalSystem.objects.all()
    serializer_class = ExternalSystemSerializer
    permission_classes = [IsAdmin]


class SyncEventViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = SyncEventSerializer
    permission_classes = [IsStaffOrAdmin]

    def get_queryset(self):
        queryset = SyncEvent.objects.all()
        after_id = self.request.query_params.get("after_id")
        if after_id:
            queryset = queryset.filter(id__gt=after_id)
        return queryset

    @action(detail=False, methods=["get"])
    def latest_cursor(self, request):
        latest = SyncEvent.objects.order_by("-id").first()
        return Response({"latest_id": latest.id if latest else 0})

    @action(detail=True, methods=["post"], permission_classes=[IsStaffOrAdmin])
    def acknowledge(self, request, pk=None):
        event = self.get_object()
        serializer = SyncEventAckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        status_value = serializer.validated_data["status"]
        if status_value == "delivered":
            mark_sync_event_delivered(event=event)
        else:
            mark_sync_event_failed(event=event, error_message=serializer.validated_data.get("error"))
        return Response(SyncEventSerializer(event).data)

    @action(detail=False, methods=["post"], permission_classes=[IsAdmin])
    def retry_due(self, request):
        retried = retry_due_sync_events()
        return Response({"retried_events": retried})
