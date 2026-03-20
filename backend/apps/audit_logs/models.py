from django.conf import settings
from django.db import models

from common.models import BaseModel


class AuditLog(BaseModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    actor_role = models.CharField(max_length=20, blank=True, null=True)
    action = models.CharField(max_length=120)
    target_type = models.CharField(max_length=120, blank=True, null=True)
    target_id = models.CharField(max_length=64, blank=True, null=True)
    target_label = models.CharField(max_length=255, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.action} ({self.created_at:%Y-%m-%d %H:%M:%S})"
