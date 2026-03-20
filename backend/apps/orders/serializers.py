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
        fields = "__all__"
        read_only_fields = ("item_name", "station", "unit_price")


class OrderStatusLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.display_name", read_only=True)

    class Meta:
        model = OrderStatusLog
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    status_logs = OrderStatusLogSerializer(many=True, read_only=True)

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
        items = self.initial_data.get("items", [])
        is_bulk_order = attrs.get("is_bulk_order", getattr(self.instance, "is_bulk_order", False))
        for item in items:
            quantity = int(item["quantity"])
            if quantity < 1:
                raise serializers.ValidationError("Order quantities must be at least 1.")
            if not is_bulk_order and quantity > 20:
                raise serializers.ValidationError("Normal orders cannot exceed 20 per item. Use bulk ordering instead.")
        return attrs

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        request = self.context["request"]
        return create_or_update_draft_order(
            actor=request.user if request.user.is_authenticated else None,
            order=None,
            order_data=validated_data,
            items_data=items,
        )

    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        request = self.context["request"]
        return create_or_update_draft_order(
            actor=request.user if request.user.is_authenticated else None,
            order=instance,
            order_data=validated_data,
            items_data=items,
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
    status = serializers.ChoiceField(choices=["payment_pending", "paid", "awaiting_verification"])

    def save(self, **kwargs):
        return set_cashier_status(
            order=self.context["order"],
            status_value=self.validated_data["status"],
            actor=self.context["request"].user,
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
