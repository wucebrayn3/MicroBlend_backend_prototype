from django.conf import settings
from django.db import models

from common.models import BaseModel


class GeneratedReport(BaseModel):
    RANGE_DAILY = "daily"
    RANGE_WEEKLY = "weekly"
    RANGE_MONTHLY = "monthly"
    RANGE_ANNUAL = "annual"
    RANGE_CUSTOM = "custom"

    RANGE_CHOICES = (
        (RANGE_DAILY, "Daily"),
        (RANGE_WEEKLY, "Weekly"),
        (RANGE_MONTHLY, "Monthly"),
        (RANGE_ANNUAL, "Annual"),
        (RANGE_CUSTOM, "Custom"),
    )

    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    range_type = models.CharField(max_length=20, choices=RANGE_CHOICES)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.range_type} report {self.created_at:%Y-%m-%d}"


class CostSimulation(BaseModel):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    assumptions = models.JSONField(default=dict, blank=True)
    results = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Simulation {self.pk}"
