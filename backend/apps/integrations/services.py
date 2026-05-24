from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.integrations.models import SyncEvent


def publish_sync_event(*, event_type, aggregate_type, aggregate_id, payload=None, source_system=None, idempotency_key=None):
    return SyncEvent.objects.create(
        source_system=source_system,
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=str(aggregate_id),
        payload=payload or {},
        idempotency_key=idempotency_key,
    )


def mark_sync_event_delivered(*, event, attempted_at=None):
    event.delivery_status = SyncEvent.STATUS_DELIVERED
    event.last_attempt_at = attempted_at or timezone.now()
    event.next_retry_at = None
    event.last_error = None
    event.save(update_fields=["delivery_status", "last_attempt_at", "next_retry_at", "last_error", "updated_at"])
    return event


def mark_sync_event_failed(*, event, error_message=None, attempted_at=None):
    attempted_at = attempted_at or timezone.now()
    max_retries = int(getattr(settings, "SYNC_RETRY_MAX_ATTEMPTS", 8))
    base_seconds = int(getattr(settings, "SYNC_RETRY_BASE_SECONDS", 10))

    event.last_attempt_at = attempted_at
    event.retry_count += 1
    event.last_error = (error_message or "Sync delivery failed.")[:255]

    if event.retry_count >= max_retries:
        event.delivery_status = SyncEvent.STATUS_DROPPED
        event.next_retry_at = None
    else:
        backoff = base_seconds * (2 ** max(0, event.retry_count - 1))
        event.delivery_status = SyncEvent.STATUS_RETRY
        event.next_retry_at = attempted_at + timedelta(seconds=backoff)

    event.save(
        update_fields=[
            "delivery_status",
            "retry_count",
            "last_attempt_at",
            "next_retry_at",
            "last_error",
            "updated_at",
        ]
    )
    return event


@transaction.atomic
def retry_due_sync_events(*, now=None, limit=200):
    now = now or timezone.now()
    due_events = (
        SyncEvent.objects.select_for_update()
        .filter(delivery_status=SyncEvent.STATUS_RETRY, next_retry_at__lte=now)
        .order_by("next_retry_at", "id")[:limit]
    )
    retried = 0
    for event in due_events:
        event.delivery_status = SyncEvent.STATUS_PENDING
        event.save(update_fields=["delivery_status", "updated_at"])
        retried += 1
    return retried
