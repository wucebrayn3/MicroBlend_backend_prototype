from django.conf import settings
from django.db import models

from common.models import BaseModel


class TableSession(BaseModel):
    SOURCE_QR = "qr"
    SOURCE_WALK_IN = "walk_in"
    SOURCE_WAITER = "waiter"
    SOURCE_MANUAL = "manual"

    SOURCE_CHOICES = (
        (SOURCE_QR, "QR"),
        (SOURCE_WALK_IN, "Walk In"),
        (SOURCE_WAITER, "Waiter"),
        (SOURCE_MANUAL, "Manual"),
    )

    table = models.ForeignKey("tables.Table", on_delete=models.CASCADE, related_name="sessions")
    merge_group = models.ForeignKey(
        "tables.TableMergeGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
    )
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    customer_account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="table_sessions",
    )
    scan_request = models.ForeignKey(
        "tables.TableScanRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_sessions",
    )
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_MANUAL)
    party_size = models.PositiveIntegerField(default=1)
    guest_label = models.CharField(max_length=120, blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-started_at",)

    @property
    def table_group(self):
        return self.merge_group

    @table_group.setter
    def table_group(self, value):
        self.merge_group = value

    def __str__(self):
        return f"Session {self.id} - {self.table.identifier}"
