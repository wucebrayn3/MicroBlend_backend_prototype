from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.notifications.models import DebounceRecord, Notification


def create_role_notification(*, title, message, role_target, category="general", metadata=None):
    return Notification.objects.create(
        role_target=role_target,
        title=title,
        message=message,
        category=category,
        metadata=metadata or {},
    )


def create_user_notification(*, title, message, recipient, category="general", metadata=None):
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        category=category,
        metadata=metadata or {},
    )


def enforce_debounce(*, actor_key, action, window_seconds, object_key=None):
    record, created = DebounceRecord.objects.get_or_create(
        actor_key=actor_key,
        action=action,
        object_key=object_key,
    )
    if not created and record.updated_at and timezone.now() - record.updated_at < timedelta(seconds=window_seconds):
        raise ValidationError(f"Action '{action}' is temporarily rate-limited. Please wait and try again.")
    record.save()
    return record
