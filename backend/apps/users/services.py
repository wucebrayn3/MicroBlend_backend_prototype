from uuid import uuid4

from django.conf import settings
from django.utils import timezone

from apps.users.models import User
from common.constants import ROLE_CUSTOMER


def get_or_create_guest_user(*, guest_key, guest_name=None):
    key = (guest_key or "").strip()
    if not key:
        raise ValueError("guest_key is required for guest ordering.")

    expires_at = timezone.now() + timezone.timedelta(hours=getattr(settings, "GUEST_ACCESS_HOURS", 12))
    user, created = User.objects.get_or_create(
        registered_device_id=key,
        defaults={
            "username": f"guest_{uuid4().hex[:12]}",
            "role": ROLE_CUSTOMER,
            "is_guest": True,
            "is_active": True,
            "guest_expires_at": expires_at,
        },
    )
    if not user.is_guest:
        # Existing non-guest account is using this device key; use that account as actor.
        return user
    if not created and user.guest_expires_at and user.guest_expires_at <= timezone.now():
        # Expired guest access is archived and a fresh guest identity is created.
        user.registered_device_id = f"expired:{user.id}:{uuid4().hex[:8]}"
        user.is_active = False
        user.is_deleted = True
        user.save(update_fields=["registered_device_id", "is_active", "is_deleted", "updated_at"])
        user = User.objects.create(
            username=f"guest_{uuid4().hex[:12]}",
            role=ROLE_CUSTOMER,
            is_guest=True,
            is_active=True,
            registered_device_id=key,
            guest_expires_at=expires_at,
        )
    elif user.guest_expires_at is None:
        user.guest_expires_at = expires_at
        user.save(update_fields=["guest_expires_at", "updated_at"])
    if guest_name and not user.first_name:
        user.first_name = guest_name[:150]
        user.save(update_fields=["first_name", "updated_at"])
    return user
