from django.db import models

from common.models import BaseModel


class ExternalSystem(BaseModel):
    SYSTEM_POS = "pos"
    SYSTEM_MOBILE = "mobile"
    SYSTEM_KIOSK = "kiosk"

    SYSTEM_CHOICES = (
        (SYSTEM_POS, "POS"),
        (SYSTEM_MOBILE, "Mobile"),
        (SYSTEM_KIOSK, "Kiosk"),
    )

    name = models.CharField(max_length=120, unique=True)
    system_type = models.CharField(max_length=20, choices=SYSTEM_CHOICES)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SyncEvent(BaseModel):
    source_system = models.ForeignKey(ExternalSystem, null=True, blank=True, on_delete=models.SET_NULL)
    event_type = models.CharField(max_length=80)
    aggregate_type = models.CharField(max_length=80)
    aggregate_id = models.CharField(max_length=64)
    payload = models.JSONField(default=dict, blank=True)
    idempotency_key = models.CharField(max_length=120, unique=True, blank=True, null=True)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return f"{self.event_type} {self.aggregate_type}:{self.aggregate_id}"
