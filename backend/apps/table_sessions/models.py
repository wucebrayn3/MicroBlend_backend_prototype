from django.db import models
from apps.tables.models import Table
from django.conf import settings
from common.models import BaseModel

class TableSession(BaseModel):
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Session - Table {self.table.number}"