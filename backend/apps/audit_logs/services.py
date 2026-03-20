from apps.audit_logs.models import AuditLog


def log_user_action(actor, action, metadata=None, target=None):
    target_type = None
    target_id = None
    target_label = None
    if target is not None:
        target_type = target.__class__.__name__
        target_id = str(target.pk)
        target_label = str(target)

    return AuditLog.objects.create(
        actor=actor,
        actor_role=getattr(actor, "staff_role", None) or getattr(actor, "role", None),
        action=action,
        target_type=target_type,
        target_id=target_id,
        target_label=target_label,
        metadata=metadata or {},
    )
