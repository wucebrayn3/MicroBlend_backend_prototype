from django.conf import settings
from django.db import models

from common.models import BaseModel


class Notification(BaseModel):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    role_target = models.CharField(max_length=20, blank=True, null=True)
    title = models.CharField(max_length=150)
    message = models.TextField()
    category = models.CharField(max_length=50, default="general")
    metadata = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title


class DebounceRecord(BaseModel):
    actor_key = models.CharField(max_length=120)
    action = models.CharField(max_length=80)
    object_key = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        unique_together = ("actor_key", "action", "object_key")

    def __str__(self):
        return f"{self.actor_key}:{self.action}:{self.object_key}"
