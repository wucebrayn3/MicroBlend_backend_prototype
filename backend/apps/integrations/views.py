from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import IsAdmin, IsStaffOrAdmin

from .models import ExternalSystem, SyncEvent
from .serializers import ExternalSystemSerializer, SyncEventSerializer


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
