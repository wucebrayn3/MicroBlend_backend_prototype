from django.conf import settings
from django.db import models

from common.models import BaseModel


class FeedbackEntry(BaseModel):
    TYPE_FEEDBACK = "feedback"
    TYPE_REPORT = "report"

    TYPE_CHOICES = (
        (TYPE_FEEDBACK, "Feedback"),
        (TYPE_REPORT, "Report"),
    )

    STATUS_OPEN = "open"
    STATUS_REVIEWED = "reviewed"
    STATUS_RESOLVED = "resolved"

    STATUS_CHOICES = (
        (STATUS_OPEN, "Open"),
        (STATUS_REVIEWED, "Reviewed"),
        (STATUS_RESOLVED, "Resolved"),
    )

    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, null=True, blank=True)
    entry_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_FEEDBACK)
    subject = models.CharField(max_length=150)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.subject
