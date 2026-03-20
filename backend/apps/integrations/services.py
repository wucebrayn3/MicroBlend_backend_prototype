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
