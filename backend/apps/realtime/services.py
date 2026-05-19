from django.db import models

from apps.realtime.models import RealtimeEvent
from apps.users.models import User


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


def get_guest_event_queryset(*, guest_key, after_id=0):
    key = (guest_key or "").strip()
    if not key:
        return RealtimeEvent.objects.none()
    guest_user = User.objects.filter(
        is_guest=True,
        is_active=True,
        registered_device_id=key,
    ).first()
    if not guest_user:
        return RealtimeEvent.objects.none()
    return RealtimeEvent.objects.filter(id__gt=after_id).filter(models.Q(user=guest_user) | models.Q(user__isnull=True, role_target__isnull=True))
