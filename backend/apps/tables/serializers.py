from django.utils import timezone
from rest_framework import serializers

from apps.audit_logs.services import log_user_action
from apps.notifications.services import create_role_notification
from apps.realtime.services import publish_realtime_event
from apps.table_sessions.models import TableSession
from apps.tables.models import StaffPageRequest, Table, TableMergeGroup, TableScanRequest
from common.constants import PAGE_STATUS_FINISHED, ROLE_CUSTOMER, SCAN_STATUS_APPROVED, SCAN_STATUS_BLOCKED, TABLE_STATUS_OCCUPIED, TABLE_STATUS_VACANT


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = "__all__"


class TableGroupSerializer(serializers.ModelSerializer):
    combined_capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = TableMergeGroup
        fields = "__all__"

    def create(self, validated_data):
        tables = validated_data.pop("tables", [])
        table_group = TableMergeGroup.objects.create(**validated_data)
        table_group.tables.set(tables)
        Table.objects.filter(id__in=[table.id for table in tables]).update(status="merged")
        actor = self.context["request"].user
        log_user_action(actor, "tables.grouped", {"table_ids": [table.id for table in tables]}, table_group)
        return table_group


# Backward compatibility alias while clients migrate from "merge" to "group".
TableMergeGroupSerializer = TableGroupSerializer


class TableScanRequestSerializer(serializers.ModelSerializer):
    table_session_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TableScanRequest
        fields = "__all__"
        read_only_fields = ("status", "blocked_reason")

    def get_table_session_id(self, obj):
        active_session = TableSession.objects.filter(table=obj.table, is_active=True).order_by("-started_at").first()
        return active_session.id if active_session else None

    def create(self, validated_data):
        request = self.context.get("request")
        actor = request.user if request and request.user.is_authenticated else None
        table = validated_data["table"]
        validated_data["status"] = SCAN_STATUS_APPROVED
        scan_request = super().create(validated_data)

        active_session = TableSession.objects.filter(table=table, is_active=True).order_by("-started_at").first()
        if not active_session:
            active_session = TableSession.objects.create(
                table=table,
                opened_by=actor,
                customer_account=actor if actor and actor.role == ROLE_CUSTOMER else None,
                scan_request=scan_request,
                source=TableSession.SOURCE_QR,
                party_size=1,
                guest_label=validated_data.get("requested_device_id") if not actor else None,
            )
        elif not active_session.scan_request_id:
            active_session.scan_request = scan_request
            active_session.save(update_fields=["scan_request", "updated_at"])

        table.status = TABLE_STATUS_OCCUPIED
        table.save(update_fields=["status", "updated_at"])

        publish_realtime_event(
            event_type="table.scan_claimed",
            payload={
                "scan_request_id": scan_request.id,
                "table_id": scan_request.table_id,
                "requested_device_id": scan_request.requested_device_id,
                "status": scan_request.status,
                "session_id": active_session.id,
            },
            role_targets=["waiter", "cashier", "kitchen", "bar", "admin"],
            users=[scan_request.requested_by] if scan_request.requested_by else None,
        )
        return scan_request


class TableScanModerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableScanRequest
        fields = ("status", "blocked_reason", "note")

    def validate_status(self, value):
        if value != SCAN_STATUS_BLOCKED:
            raise serializers.ValidationError("Only blocking is supported. Table claims are auto-approved.")
        return value

    def update(self, instance, validated_data):
        instance.status = validated_data["status"]
        instance.blocked_reason = validated_data.get("blocked_reason")
        instance.note = validated_data.get("note", instance.note)
        instance.save()
        table_status = TABLE_STATUS_OCCUPIED if instance.status == SCAN_STATUS_APPROVED else TABLE_STATUS_VACANT
        instance.table.status = table_status
        instance.table.save(update_fields=["status", "updated_at"])
        if instance.status == SCAN_STATUS_BLOCKED:
            active_sessions = TableSession.objects.filter(table=instance.table, is_active=True)
            for session in active_sessions:
                session.is_active = False
                session.ended_at = timezone.now()
                session.save(update_fields=["is_active", "ended_at", "updated_at"])
        log_user_action(self.context["request"].user, f"table.scan.{instance.status}", {"scan_request_id": instance.id}, instance.table)
        publish_realtime_event(
            event_type="table.scan_request_moderated",
            payload={
                "scan_request_id": instance.id,
                "table_id": instance.table_id,
                "status": instance.status,
                "blocked_reason": instance.blocked_reason,
            },
            role_targets=["waiter", "cashier", "kitchen", "bar", "admin"],
            users=[instance.requested_by] if instance.requested_by else None,
        )
        return instance


class StaffPageRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffPageRequest
        fields = "__all__"

    def create(self, validated_data):
        page_request = super().create(validated_data)
        create_role_notification(
            title="Staff page request",
            message=f"Table assistance requested for {page_request.reason}.",
            role_target="staff",
            metadata={"page_request_id": page_request.id, "table_id": page_request.table_id},
        )
        publish_realtime_event(
            event_type="staff.page_requested",
            payload={"page_request_id": page_request.id, "table_id": page_request.table_id, "reason": page_request.reason},
            role_targets=["waiter", "cashier", "kitchen", "bar", "admin"],
        )
        return page_request


class StaffPageFinishSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffPageRequest
        fields = ("status",)

    def validate_status(self, value):
        if value != PAGE_STATUS_FINISHED:
            raise serializers.ValidationError("Page requests can only be marked as finished here.")
        return value

    def update(self, instance, validated_data):
        instance.status = PAGE_STATUS_FINISHED
        instance.resolved_by = self.context["request"].user
        instance.save(update_fields=["status", "resolved_by", "updated_at"])
        log_user_action(self.context["request"].user, "staff.page.finished", {"page_request_id": instance.id}, instance)
        publish_realtime_event(
            event_type="staff.page_finished",
            payload={"page_request_id": instance.id, "table_id": instance.table_id, "status": instance.status},
            role_targets=["waiter", "cashier", "kitchen", "bar", "admin"],
        )
        return instance
