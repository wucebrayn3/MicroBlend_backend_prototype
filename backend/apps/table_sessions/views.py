from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.table_sessions.models import TableSession
from apps.table_sessions.serializers import CloseTableSessionSerializer, TableSessionSerializer
from common.permissions import IsStaffOrAdmin


class TableSessionViewSet(viewsets.ModelViewSet):
    queryset = TableSession.objects.select_related("table", "merge_group", "opened_by", "customer_account").all()
    serializer_class = TableSessionSerializer
    permission_classes = [IsStaffOrAdmin]

    @action(detail=True, methods=["post"], permission_classes=[IsStaffOrAdmin])
    def close(self, request, pk=None):
        session = self.get_object()
        serializer = CloseTableSessionSerializer(session, data={"is_active": False}, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TableSessionSerializer(session).data, status=status.HTTP_200_OK)
