from rest_framework import serializers

from apps.audit_logs.services import log_user_action
from apps.notifications.services import create_role_notification
from apps.tables.models import StaffPageRequest, Table, TableMergeGroup, TableScanRequest
from common.constants import PAGE_STATUS_FINISHED, SCAN_STATUS_APPROVED, SCAN_STATUS_BLOCKED, TABLE_STATUS_OCCUPIED, TABLE_STATUS_VACANT


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = "__all__"


class TableMergeGroupSerializer(serializers.ModelSerializer):
    combined_capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = TableMergeGroup
        fields = "__all__"

    def create(self, validated_data):
        tables = validated_data.pop("tables", [])
        merge_group = TableMergeGroup.objects.create(**validated_data)
        merge_group.tables.set(tables)
        Table.objects.filter(id__in=[table.id for table in tables]).update(status="merged")
        actor = self.context["request"].user
        log_user_action(actor, "tables.merged", {"table_ids": [table.id for table in tables]}, merge_group)
        return merge_group


class TableScanRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableScanRequest
        fields = "__all__"
        read_only_fields = ("status", "blocked_reason")


class TableScanModerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TableScanRequest
        fields = ("status", "blocked_reason", "note")

    def validate_status(self, value):
        if value not in {SCAN_STATUS_APPROVED, SCAN_STATUS_BLOCKED}:
            raise serializers.ValidationError("Invalid moderation status.")
        return value

    def update(self, instance, validated_data):
        instance.status = validated_data["status"]
        instance.blocked_reason = validated_data.get("blocked_reason")
        instance.note = validated_data.get("note", instance.note)
        instance.save()
        table_status = TABLE_STATUS_OCCUPIED if instance.status == SCAN_STATUS_APPROVED else TABLE_STATUS_VACANT
        instance.table.status = table_status
        instance.table.save(update_fields=["status", "updated_at"])
        log_user_action(self.context["request"].user, f"table.scan.{instance.status}", {"scan_request_id": instance.id}, instance.table)
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
        return instance
