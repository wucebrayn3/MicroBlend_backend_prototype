from django.db import models

from apps.realtime.models import RealtimeEvent


def publish_realtime_event(*, event_type, payload=None, role_targets=None, users=None):
    payload = payload or {}
    events = [RealtimeEvent(event_type=event_type, payload=payload)]

    if role_targets:
        events.extend(RealtimeEvent(event_type=event_type, payload=payload, role_target=role) for role in role_targets)

    if users:
        events.extend(RealtimeEvent(event_type=event_type, payload=payload, user=user) for user in users)

    RealtimeEvent.objects.bulk_create(events)


def get_user_event_queryset(user, after_id=0):
    role_targets = {user.role}
    if user.staff_role:
        role_targets.add(user.staff_role)
    if user.role == "staff":
        role_targets.add("staff")
    return RealtimeEvent.objects.filter(id__gt=after_id).filter(
        models.Q(role_target__isnull=True, user__isnull=True)
        | models.Q(role_target__in=role_targets)
        | models.Q(user=user)
    )
