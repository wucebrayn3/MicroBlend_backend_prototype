from django.conf import settings
from django.db import models

from common.models import BaseModel


class RealtimeEvent(BaseModel):
    event_type = models.CharField(max_length=120)
    payload = models.JSONField(default=dict, blank=True)
    role_target = models.CharField(max_length=20, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return f"{self.id}:{self.event_type}"
