from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import IsAdmin
from common.utils import get_date_range

from .models import CostSimulation, GeneratedReport
from .serializers import (
    CostSimulationRequestSerializer,
    CostSimulationSerializer,
    GeneratedReportSerializer,
    ReportRequestSerializer,
)
from .services import backup_database, build_dashboard_snapshot, generate_report, reset_database, run_cost_simulation


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAdmin]

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        range_type = request.query_params.get("range", "daily")
        start_at, end_at = get_date_range(range_type)
        return Response(build_dashboard_snapshot(start_at, end_at))

    @action(detail=False, methods=["post"])
    def reports(self, request):
        serializer = ReportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = generate_report(actor=request.user, **serializer.validated_data)
        return Response(GeneratedReportSerializer(report).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def simulate(self, request):
        serializer = CostSimulationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        simulation = run_cost_simulation(actor=request.user, **serializer.validated_data)
        return Response(CostSimulationSerializer(simulation).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def backup(self, request):
        backup_path = backup_database(actor=request.user)
        return Response({"backup_path": str(backup_path)}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def reset(self, request):
        backup_path = reset_database(actor=request.user)
        return Response({"backup_path": str(backup_path), "status": "database reset"}, status=status.HTTP_200_OK)


class GeneratedReportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GeneratedReport.objects.select_related("generated_by").all()
    serializer_class = GeneratedReportSerializer
    permission_classes = [IsAdmin]


class CostSimulationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CostSimulation.objects.select_related("created_by").all()
    serializer_class = CostSimulationSerializer
    permission_classes = [IsAdmin]
