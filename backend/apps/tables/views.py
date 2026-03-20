from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.tables.models import StaffPageRequest, Table, TableMergeGroup, TableScanRequest
from apps.tables.serializers import (
    StaffPageFinishSerializer,
    StaffPageRequestSerializer,
    TableMergeGroupSerializer,
    TableScanModerationSerializer,
    TableScanRequestSerializer,
    TableSerializer,
)
from common.permissions import IsStaffOrAdmin, build_staff_role_permission


class TableViewSet(viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [AllowAny()]
        return [IsStaffOrAdmin()]

    @action(detail=True, methods=["post"], permission_classes=[IsStaffOrAdmin])
    def mark_occupied(self, request, pk=None):
        table = self.get_object()
        table.status = "occupied"
        table.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(table).data)

    @action(detail=True, methods=["post"], permission_classes=[IsStaffOrAdmin])
    def mark_vacant(self, request, pk=None):
        table = self.get_object()
        table.status = "vacant"
        table.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(table).data)


class TableMergeGroupViewSet(viewsets.ModelViewSet):
    queryset = TableMergeGroup.objects.prefetch_related("tables").all()
    serializer_class = TableMergeGroupSerializer
    permission_classes = [IsStaffOrAdmin]


class TableScanRequestViewSet(viewsets.ModelViewSet):
    queryset = TableScanRequest.objects.select_related("table", "requested_by").all()

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsStaffOrAdmin()]

    def get_serializer_class(self):
        if self.action == "moderate":
            return TableScanModerationSerializer
        return TableScanRequestSerializer

    @action(detail=True, methods=["post"], permission_classes=[IsStaffOrAdmin])
    def moderate(self, request, pk=None):
        scan_request = self.get_object()
        serializer = self.get_serializer(scan_request, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TableScanRequestSerializer(scan_request).data)


class StaffPageRequestViewSet(viewsets.ModelViewSet):
    queryset = StaffPageRequest.objects.select_related("table", "session", "requested_by", "resolved_by").all()
    serializer_class = StaffPageRequestSerializer

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [build_staff_role_permission("waiter", "cashier", "kitchen", "bar")()]

    @action(detail=True, methods=["post"], permission_classes=[build_staff_role_permission("waiter", "cashier", "kitchen", "bar")])
    def finish(self, request, pk=None):
        page_request = self.get_object()
        serializer = StaffPageFinishSerializer(page_request, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StaffPageRequestSerializer(page_request).data, status=status.HTTP_200_OK)
