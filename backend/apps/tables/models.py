from django.conf import settings
from django.db import models

from common.constants import (
    PAGE_REASON_CHOICES,
    PAGE_STATUS_CHOICES,
    SCAN_STATUS_CHOICES,
    TABLE_STATUS_CHOICES,
    TABLE_STATUS_OCCUPIED,
    TABLE_STATUS_VACANT,
)
from common.models import BaseModel
from common.utils import generate_reference


class Table(BaseModel):
    identifier = models.CharField(max_length=30, unique=True)
    capacity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=TABLE_STATUS_CHOICES, default=TABLE_STATUS_VACANT)
    zone = models.CharField(max_length=100, blank=True, null=True)
    qr_code_value = models.CharField(max_length=64, unique=True, default="", blank=True)

    class Meta:
        ordering = ("identifier",)

    def save(self, *args, **kwargs):
        if not self.qr_code_value:
            self.qr_code_value = generate_reference("TABLEQR")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.identifier


class TableMergeGroup(BaseModel):
    name = models.CharField(max_length=64, unique=True, default="", blank=True)
    tables = models.ManyToManyField(Table, related_name="merge_groups")
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = generate_reference("MERGE")
        super().save(*args, **kwargs)

    @property
    def combined_capacity(self):
        return self.tables.aggregate(total=models.Sum("capacity"))["total"] or 0

    def __str__(self):
        return self.name


class TableScanRequest(BaseModel):
    table = models.ForeignKey(Table, related_name="scan_requests", on_delete=models.CASCADE)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    requested_device_id = models.CharField(max_length=128, blank=True, null=True)
    status = models.CharField(max_length=20, choices=SCAN_STATUS_CHOICES, default="pending")
    note = models.CharField(max_length=255, blank=True, null=True)
    blocked_reason = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.table.identifier} scan {self.status}"


class StaffPageRequest(BaseModel):
    table = models.ForeignKey(Table, null=True, blank=True, on_delete=models.SET_NULL, related_name="page_requests")
    session = models.ForeignKey(
        "table_sessions.TableSession",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="page_requests",
    )
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    reason = models.CharField(max_length=20, choices=PAGE_REASON_CHOICES)
    status = models.CharField(max_length=20, choices=PAGE_STATUS_CHOICES, default="pending")
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resolved_page_requests",
    )

    class Meta:
        ordering = ("status", "-created_at")

    def __str__(self):
        return f"{self.reason} - {self.status}"
