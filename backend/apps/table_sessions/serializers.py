from django.utils import timezone
from rest_framework import serializers

from apps.audit_logs.services import log_user_action
from apps.realtime.services import publish_realtime_event
from apps.table_sessions.models import TableSession
from apps.tables.models import TableMergeGroup


class TableSessionSerializer(serializers.ModelSerializer):
    table_group = serializers.PrimaryKeyRelatedField(
        source="merge_group",
        queryset=TableMergeGroup.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = TableSession
        fields = (
            "id",
            "table",
            "merge_group",
            "table_group",
            "opened_by",
            "customer_account",
            "scan_request",
            "source",
            "party_size",
            "guest_label",
            "started_at",
            "ended_at",
            "is_active",
            "created_at",
            "updated_at",
        )

    def create(self, validated_data):
        session = super().create(validated_data)
        session.table.status = "occupied"
        session.table.save(update_fields=["status", "updated_at"])
        actor = self.context["request"].user if self.context.get("request") and self.context["request"].user.is_authenticated else None
        if actor:
            log_user_action(actor, "table_session.opened", {"table_id": session.table_id}, session)
        publish_realtime_event(
            event_type="table.session_opened",
            payload={
                "session_id": session.id,
                "table_id": session.table_id,
                "party_size": session.party_size,
                "source": session.source,
            },
            role_targets=["waiter", "cashier", "kitchen", "bar", "admin"],
            users=[session.customer_account] if session.customer_account else None,
        )
        return session


class CloseTableSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableSession
        fields = ("is_active",)

    def validate_is_active(self, value):
        if value is not False:
            raise serializers.ValidationError("This action only closes a session.")
        return value

    def update(self, instance, validated_data):
        instance.is_active = False
        instance.ended_at = timezone.now()
        instance.save(update_fields=["is_active", "ended_at", "updated_at"])
        instance.table.status = "vacant"
        instance.table.save(update_fields=["status", "updated_at"])
        log_user_action(self.context["request"].user, "table_session.closed", {"table_id": instance.table_id}, instance)
        publish_realtime_event(
            event_type="table.session_closed",
            payload={"session_id": instance.id, "table_id": instance.table_id},
            role_targets=["waiter", "cashier", "kitchen", "bar", "admin"],
            users=[instance.customer_account] if instance.customer_account else None,
        )
        return instance
