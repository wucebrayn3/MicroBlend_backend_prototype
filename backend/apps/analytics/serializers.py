from decimal import Decimal

from rest_framework import serializers

from .models import CostSimulation, GeneratedReport


class GeneratedReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedReport
        fields = "__all__"
        read_only_fields = ("generated_by", "payload", "start_at", "end_at")


class CostSimulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostSimulation
        fields = "__all__"
        read_only_fields = ("created_by", "results")


class ReportRequestSerializer(serializers.Serializer):
    range_type = serializers.ChoiceField(choices=["daily", "weekly", "monthly", "annual", "custom"])
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)


class CostSimulationRequestSerializer(serializers.Serializer):
    menu_price_delta = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    monthly_salary_delta = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    staff_delta = serializers.IntegerField(default=0)
    expansion_cost = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    added_capacity = serializers.IntegerField(default=0)
