from collections import defaultdict
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction

from apps.audit_logs.services import log_user_action
from apps.integrations.services import publish_sync_event
from apps.inventory.services import consume_ingredient
from apps.menu.models import MenuItem, MenuItemIngredient
from apps.notifications.services import create_role_notification, create_user_notification, enforce_debounce
from apps.orders.models import Order, OrderItem, OrderStatusLog
from common.constants import (
    ORDER_CHANNEL_CUSTOMER,
    ORDER_CHANNEL_WAITER,
    ORDER_STATUS_CANCELLED,
    ORDER_STATUS_PAID,
    ORDER_STATUS_PAYMENT_PENDING,
    ORDER_STATUS_PLACED,
    ORDER_STATUS_PREPARING,
    ORDER_STATUS_READY,
    STATION_BAR,
    STATION_KITCHEN,
    WORKFLOW_STATUS_AWAITING_VERIFICATION,
    WORKFLOW_STATUS_NOT_REQUIRED,
    WORKFLOW_STATUS_PAID,
    WORKFLOW_STATUS_PENDING,
    WORKFLOW_STATUS_PREPARING,
    WORKFLOW_STATUS_READY,
)


def _actor_key(actor):
    return f"user:{actor.id}" if actor else "guest"


def _resolve_actor_snapshot(actor):
    if not actor:
        return None, None
    return actor.display_name, actor.staff_role or actor.role


def _order_price_threshold():
    return getattr(settings, "ORDER_PRICE_ALERT_THRESHOLD", Decimal("2500.00"))


def _station_items(order, station):
    return order.items.filter(station=station)


def _validate_editable(order):
    locked_statuses = {WORKFLOW_STATUS_PREPARING, WORKFLOW_STATUS_READY}
    if order.kitchen_status in locked_statuses or order.bar_status in locked_statuses:
        raise ValidationError("This order can no longer be edited because preparation has started.")


def _deduct_inventory_for_station(order, station, actor):
    relevant_items = _station_items(order, station).select_related("menu_item")
    requirements = defaultdict(Decimal)
    for item in relevant_items:
        for requirement in MenuItemIngredient.objects.select_related("ingredient").filter(menu_item=item.menu_item):
            requirements[requirement.ingredient] += requirement.quantity_required * item.quantity

    for ingredient, quantity in requirements.items():
        consume_ingredient(
            ingredient=ingredient,
            quantity=quantity,
            actor=actor,
            note=f"Order {order.receipt_number} {station} preparation",
            related_order_id=order.id,
        )


def _maybe_send_cashier_alert(order):
    if order.total_amount >= _order_price_threshold() and not order.price_alert_sent:
        create_role_notification(
            title="High value order alert",
            message=f"Order {order.receipt_number} exceeded the confirmation threshold.",
            role_target="cashier",
            category="order_threshold",
            metadata={"order_id": order.id, "total_amount": str(order.total_amount)},
        )
        order.price_alert_sent = True
        order.save(update_fields=["price_alert_sent", "updated_at"])


def _maybe_send_demand_alert(order):
    from django.utils import timezone

    window_start = timezone.now() - timezone.timedelta(hours=2)
    for item in order.items.select_related("menu_item"):
        recent_quantity = (
            OrderItem.objects.filter(
                menu_item=item.menu_item,
                created_at__gte=window_start,
                order__status__in=[
                    ORDER_STATUS_PLACED,
                    ORDER_STATUS_PREPARING,
                    ORDER_STATUS_READY,
                    ORDER_STATUS_PAYMENT_PENDING,
                    ORDER_STATUS_PAID,
                ],
            )
            .aggregate(total=models.Sum("quantity"))["total"]
            or 0
        )
        low_ingredient_count = sum(
            1 for requirement in item.menu_item.ingredients.select_related("ingredient") if requirement.ingredient.available_quantity <= requirement.ingredient.reorder_level
        )
        if recent_quantity >= 5 or low_ingredient_count > 0:
            create_role_notification(
                title="Demand-driven inventory alert",
                message=f"Demand for {item.menu_item.name} is rising. Please review stock before it runs out.",
                role_target=item.menu_item.preparation_station,
                category="inventory_demand",
                metadata={
                    "menu_item_id": item.menu_item_id,
                    "recent_quantity": recent_quantity,
                    "low_ingredient_count": low_ingredient_count,
                },
            )


@transaction.atomic
def create_or_update_draft_order(*, actor, order, order_data, items_data):
    actor_name, actor_role = _resolve_actor_snapshot(actor)
    channel = order_data.get("channel") or (order.channel if order else ORDER_CHANNEL_CUSTOMER)

    if actor and actor.role == "staff" and channel == ORDER_CHANNEL_CUSTOMER:
        channel = ORDER_CHANNEL_WAITER

    if order is None:
        order = Order.objects.create(
            placed_by=actor,
            placed_by_name=actor_name,
            placed_by_role=actor_role,
            channel=channel,
            **order_data,
        )
    else:
        _validate_editable(order)
        for field, value in order_data.items():
            setattr(order, field, value)
        order.placed_by = actor or order.placed_by
        order.placed_by_name = actor_name or order.placed_by_name
        order.placed_by_role = actor_role or order.placed_by_role
        order.channel = channel
        order.save()
        if items_data is not None:
            order.items.all().delete()

    if items_data is not None:
        for item_data in items_data:
            menu_item = item_data["menu_item"]
            if not isinstance(menu_item, MenuItem):
                menu_item = MenuItem.objects.get(pk=menu_item)
            menu_item.recalculate_availability(save=True)
            if not menu_item.is_available:
                raise ValidationError(f"{menu_item.name} is currently unavailable.")
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                item_name=menu_item.name,
                station=menu_item.preparation_station,
                quantity=item_data["quantity"],
                unit_price=menu_item.price,
                customization_notes=item_data.get("customization_notes"),
            )

    order.refresh_totals(save=True)
    order.initialize_station_statuses()
    order.save()
    publish_sync_event(
        event_type="order.draft_saved",
        aggregate_type="order",
        aggregate_id=order.id,
        payload={"status": order.status, "total_amount": str(order.total_amount)},
    )
    if actor:
        log_user_action(actor, "order.draft_saved", {"order_id": order.id, "channel": order.channel}, order)
    return order


def apply_playlist_to_order(*, order, playlist, actor):
    if order.items.exists():
        order.items.all().delete()
    for playlist_item in playlist.items.select_related("menu_item"):
        OrderItem.objects.create(
            order=order,
            menu_item=playlist_item.menu_item,
            item_name=playlist_item.menu_item.name,
            station=playlist_item.menu_item.preparation_station,
            quantity=playlist_item.quantity,
            unit_price=playlist_item.menu_item.price,
        )
    order.refresh_totals(save=True)
    log_user_action(actor, "order.playlist_applied", {"order_id": order.id, "playlist_id": playlist.id}, order)
    return order


@transaction.atomic
def submit_order(order, actor=None):
    enforce_debounce(
        actor_key=_actor_key(actor),
        action="order.submit",
        object_key=f"order:{order.id}",
        window_seconds=getattr(settings, "ORDER_SUBMIT_DEBOUNCE_SECONDS", 5),
    )
    if not order.items.exists():
        raise ValidationError("Orders must contain at least one item before submission.")

    if order.status == ORDER_STATUS_CANCELLED:
        raise ValidationError("Cancelled orders cannot be submitted.")

    order.status = ORDER_STATUS_PLACED
    order.initialize_station_statuses()
    if order.is_bulk_order:
        order.requires_cashier_verification = True
        order.cashier_status = WORKFLOW_STATUS_AWAITING_VERIFICATION
    order.save()
    OrderStatusLog.objects.create(order=order, actor=actor, status=ORDER_STATUS_PLACED)
    publish_sync_event(
        event_type="order.submitted",
        aggregate_type="order",
        aggregate_id=order.id,
        payload={"receipt_number": order.receipt_number, "status": order.status},
    )
    create_role_notification(
        title="New order placed",
        message=f"Order {order.receipt_number} needs cashier attention.",
        role_target="cashier",
        category="order",
        metadata={"order_id": order.id},
    )
    if order.placed_by:
        create_user_notification(
            title="Order placed",
            message=f"Your order {order.receipt_number} has been placed.",
            recipient=order.placed_by,
            category="order",
            metadata={"order_id": order.id},
        )
    _maybe_send_cashier_alert(order)
    _maybe_send_demand_alert(order)
    if actor:
        log_user_action(actor, "order.submitted", {"order_id": order.id}, order)
    return order


@transaction.atomic
def cancel_order(order, actor=None, note=None):
    _validate_editable(order)
    order.status = ORDER_STATUS_CANCELLED
    order.kitchen_status = WORKFLOW_STATUS_NOT_REQUIRED if order.kitchen_status != WORKFLOW_STATUS_NOT_REQUIRED else order.kitchen_status
    order.bar_status = WORKFLOW_STATUS_NOT_REQUIRED if order.bar_status != WORKFLOW_STATUS_NOT_REQUIRED else order.bar_status
    order.save()
    OrderStatusLog.objects.create(order=order, actor=actor, status=ORDER_STATUS_CANCELLED, note=note)
    publish_sync_event(
        event_type="order.cancelled",
        aggregate_type="order",
        aggregate_id=order.id,
        payload={"note": note},
    )
    if actor:
        log_user_action(actor, "order.cancelled", {"order_id": order.id, "note": note}, order)
    return order


@transaction.atomic
def set_station_status(*, order, station, status_value, actor):
    if station not in {STATION_KITCHEN, STATION_BAR}:
        raise ValidationError("Unsupported station.")
    station_field = f"{station}_status"
    current_status = getattr(order, station_field)
    if current_status == WORKFLOW_STATUS_NOT_REQUIRED:
        raise ValidationError(f"{station.title()} workflow is not required for this order.")

    setattr(order, station_field, status_value)
    if status_value == WORKFLOW_STATUS_PREPARING and not order.inventory_committed:
        _deduct_inventory_for_station(order, station, actor)
        order.inventory_committed = True

    relevant_statuses = {order.kitchen_status, order.bar_status}
    if WORKFLOW_STATUS_PREPARING in relevant_statuses:
        order.status = ORDER_STATUS_PREPARING
    if relevant_statuses.issubset({WORKFLOW_STATUS_READY, WORKFLOW_STATUS_NOT_REQUIRED}):
        order.status = ORDER_STATUS_READY
        order.cashier_status = WORKFLOW_STATUS_PENDING
    order.save()
    OrderStatusLog.objects.create(order=order, actor=actor, status=f"{station}.{status_value}")
    publish_sync_event(
        event_type=f"order.{station}_updated",
        aggregate_type="order",
        aggregate_id=order.id,
        payload={station_field: status_value, "status": order.status},
    )
    log_user_action(actor, f"order.{station}.{status_value}", {"order_id": order.id}, order)
    return order


@transaction.atomic
def set_cashier_status(*, order, status_value, actor):
    order.cashier_status = status_value
    if status_value == ORDER_STATUS_PAYMENT_PENDING:
        order.status = ORDER_STATUS_PAYMENT_PENDING
    elif status_value == WORKFLOW_STATUS_PAID or status_value == ORDER_STATUS_PAID:
        order.status = ORDER_STATUS_PAID
        order.cashier_status = WORKFLOW_STATUS_PAID
    order.save()
    OrderStatusLog.objects.create(order=order, actor=actor, status=f"cashier.{status_value}")
    publish_sync_event(
        event_type="order.cashier_updated",
        aggregate_type="order",
        aggregate_id=order.id,
        payload={"cashier_status": order.cashier_status, "status": order.status},
    )
    log_user_action(actor, f"order.cashier.{status_value}", {"order_id": order.id}, order)
    return order
