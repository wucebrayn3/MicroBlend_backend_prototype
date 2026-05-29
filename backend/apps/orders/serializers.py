from django.contrib.auth import authenticate
from rest_framework import serializers

from apps.menu.models import MenuItem, OrderPlaylist
from apps.orders.models import Order, OrderItem, OrderStatusLog
from apps.table_sessions.models import TableSession
from apps.orders.services import (
    apply_playlist_to_order,
    cancel_order,
    create_or_update_draft_order,
    set_cashier_status,
    set_station_status,
    submit_order,
)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = (
            "id",
            "order",
            "menu_item",
            "quantity",
            "customization_notes",
            "item_name",
            "station",
            "unit_price",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("order", "item_name", "station", "unit_price", "created_at", "updated_at")


class OrderStatusLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.display_name", read_only=True)

    class Meta:
        model = OrderStatusLog
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    status_logs = OrderStatusLogSerializer(many=True, read_only=True)
    guest_key = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = (
            "placed_by_name",
            "placed_by_role",
            "total_amount",
            "receipt_number",
            "inventory_committed",
            "status_logs",
        )

    def validate(self, attrs):
        request = self.context.get("request")
        guest_key = (self.initial_data.get("guest_key") or "").strip()
        is_bulk_order = attrs.get("is_bulk_order", getattr(self.instance, "is_bulk_order", False))
        table_session = attrs.get("table_session", getattr(self.instance, "table_session", None))
        if table_session is None:
            raise serializers.ValidationError("Ordering requires an active table session.")
        if not table_session.is_active:
            raise serializers.ValidationError("This table session is no longer active.")
        if request and not request.user.is_authenticated and not guest_key:
            raise serializers.ValidationError("guest_key is required when ordering as guest.")
        if request and not request.user.is_authenticated and is_bulk_order:
            raise serializers.ValidationError("Guest users cannot place bulk orders.")
        items = self.initial_data.get("items", [])
        for item in items:
            quantity = int(item["quantity"])
            if quantity < 1:
                raise serializers.ValidationError("Order quantities must be at least 1.")
            if not is_bulk_order and quantity > 20:
                raise serializers.ValidationError("Normal orders cannot exceed 20 per item. Use bulk ordering instead.")
        return attrs

    def create(self, validated_data):
        guest_key = validated_data.pop("guest_key", None)
        items = validated_data.pop("items", [])
        request = self.context["request"]
        return create_or_update_draft_order(
            actor=request.user if request.user.is_authenticated else None,
            order=None,
            order_data=validated_data,
            items_data=items,
            guest_key=guest_key,
        )

    def update(self, instance, validated_data):
        guest_key = validated_data.pop("guest_key", None)
        items = validated_data.pop("items", None)
        request = self.context["request"]
        return create_or_update_draft_order(
            actor=request.user if request.user.is_authenticated else None,
            order=instance,
            order_data=validated_data,
            items_data=items,
            guest_key=guest_key,
        )


class SubmitOrderSerializer(serializers.Serializer):
    pass

    def save(self, **kwargs):
        return submit_order(self.context["order"], actor=self.context["request"].user if self.context["request"].user.is_authenticated else None)


class CancelOrderSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)

    def save(self, **kwargs):
        return cancel_order(
            self.context["order"],
            actor=self.context["request"].user if self.context["request"].user.is_authenticated else None,
            note=self.validated_data.get("note"),
        )


class StationStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["preparing", "ready"])

    def save(self, **kwargs):
        return set_station_status(
            order=self.context["order"],
            station=self.context["station"],
            status_value=self.validated_data["status"],
            actor=self.context["request"].user,
        )


class CashierStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["waiting", "awaiting_payment", "paid", "unpaid"])
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)
    cashier_identifier = serializers.CharField(required=False, allow_blank=True)
    cashier_password = serializers.CharField(required=False, allow_blank=True, write_only=True)

    def validate(self, attrs):
        status_value = attrs["status"]
        order = self.context["order"]
        request_user = self.context["request"].user
        if status_value == "unpaid":
            attrs["status"] = "awaiting_payment"
            status_value = "awaiting_payment"
        if status_value == "awaiting_payment" and order.cashier_status == "paid":
            if order.status not in {"pending", "waiting"}:
                raise serializers.ValidationError("Paid orders can only be marked unpaid before preparation begins.")
            identifier = (attrs.get("cashier_identifier") or "").strip()
            password = attrs.get("cashier_password") or ""
            if not identifier or not password:
                raise serializers.ValidationError("Cashier credentials are required to mark a paid order as unpaid.")
            lookup = {"email": identifier} if "@" in identifier else {"phone": identifier}
            from apps.users.models import User
            try:
                cashier_user = User.objects.get(**lookup)
            except User.DoesNotExist as exc:
                raise serializers.ValidationError("Invalid cashier credentials.") from exc
            authenticated_user = authenticate(username=cashier_user.username, password=password)
            if not authenticated_user or not authenticated_user.is_active:
                raise serializers.ValidationError("Invalid cashier credentials.")
            if authenticated_user.id != request_user.id:
                raise serializers.ValidationError("Credentials must belong to the acting cashier.")
            if authenticated_user.role != "staff" or authenticated_user.staff_role != "cashier":
                raise serializers.ValidationError("Only cashier credentials are allowed for this action.")
            if not attrs.get("reason"):
                raise serializers.ValidationError({"reason": "A reason is required to revert a paid order."})
            attrs["credential_verified"] = True
        return attrs

    def save(self, **kwargs):
        return set_cashier_status(
            order=self.context["order"],
            status_value=self.validated_data["status"],
            actor=self.context["request"].user,
            credential_verified=self.validated_data.get("credential_verified", False),
            note=self.validated_data.get("reason"),
        )


class PlaylistOrderSerializer(serializers.Serializer):
    playlist_id = serializers.PrimaryKeyRelatedField(queryset=OrderPlaylist.objects.all(), source="playlist")
    table_session = serializers.PrimaryKeyRelatedField(queryset=TableSession.objects.all(), required=False, allow_null=True)
    placed_for_name = serializers.CharField(required=False, allow_blank=True)

    def validate_playlist(self, value):
        request = self.context["request"]
        if value.owner != request.user:
            raise serializers.ValidationError("You can only use your own order playlists.")
        return value

    def save(self, **kwargs):
        playlist = self.validated_data["playlist"]
        order = create_or_update_draft_order(
            actor=self.context["request"].user,
            order=None,
            order_data={
                "table_session": self.validated_data.get("table_session"),
                "placed_for_name": self.validated_data.get("placed_for_name"),
                "channel": "customer_account",
            },
            items_data=[],
        )
        return apply_playlist_to_order(order=order, playlist=playlist, actor=self.context["request"].user)
