from django.utils import timezone
from rest_framework import serializers

from apps.audit_logs.services import log_user_action
from apps.table_sessions.models import TableSession


class TableSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableSession
        fields = "__all__"

    def create(self, validated_data):
        session = super().create(validated_data)
        session.table.status = "occupied"
        session.table.save(update_fields=["status", "updated_at"])
        actor = self.context["request"].user if self.context.get("request") and self.context["request"].user.is_authenticated else None
        if actor:
            log_user_action(actor, "table_session.opened", {"table_id": session.table_id}, session)
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
        return instance
