from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.audit_logs.services import log_user_action
from apps.inventory.models import Ingredient, InventoryBatch, InventoryMovement
from apps.realtime.services import publish_realtime_event


def recalculate_menu_availability():
    from apps.menu.models import MenuItem

    changed_items = []
    for menu_item in MenuItem.objects.all():
        previous = menu_item.is_available
        current = menu_item.recalculate_availability(save=True)
        if previous != current:
            changed_items.append(
                {
                    "menu_item_id": menu_item.id,
                    "menu_item_name": menu_item.name,
                    "is_available": current,
                }
            )
            publish_realtime_event(
                event_type="menu.availability_changed",
                payload={
                    "menu_item_id": menu_item.id,
                    "menu_item_name": menu_item.name,
                    "is_available": current,
                },
                role_targets=["customer", "staff", "cashier", "kitchen", "bar", "waiter", "admin"],
            )
    if changed_items:
        publish_realtime_event(
            event_type="menu.availability_batch_changed",
            payload={"changed_items": changed_items},
            role_targets=["customer", "staff", "cashier", "kitchen", "bar", "waiter", "admin"],
        )
    return changed_items


def publish_ingredient_stock_event(ingredient):
    available_quantity = ingredient.available_quantity
    payload = {
        "ingredient_id": ingredient.id,
        "ingredient_name": ingredient.name,
        "unit": ingredient.unit,
        "available_quantity": str(available_quantity),
        "reorder_level": str(ingredient.reorder_level),
        "is_low": available_quantity <= ingredient.reorder_level,
        "is_out": available_quantity <= 0,
    }
    publish_realtime_event(
        event_type="inventory.ingredient_stock_changed",
        payload=payload,
        role_targets=["staff", "cashier", "kitchen", "bar", "admin"],
    )


@transaction.atomic
def restock_batch(*, ingredient, quantity, unit_cost, expiration_date, actor=None, source=None):
    batch = InventoryBatch.objects.create(
        ingredient=ingredient,
        quantity_added=quantity,
        quantity_remaining=quantity,
        unit_cost=unit_cost,
        expiration_date=expiration_date,
        source=source,
    )
    InventoryMovement.objects.create(
        ingredient=ingredient,
        batch=batch,
        movement_type=InventoryMovement.MOVEMENT_RESTOCK,
        quantity=quantity,
        actor=actor,
        note=source,
    )
    if actor:
        log_user_action(actor, "inventory.restocked", {"ingredient_id": ingredient.id, "quantity": str(quantity)}, ingredient)
    recalculate_menu_availability()
    publish_ingredient_stock_event(ingredient)
    publish_realtime_event(
        event_type="inventory.batch_restocked",
        payload={
            "ingredient_id": ingredient.id,
            "batch_id": batch.id,
            "quantity_added": str(quantity),
            "unit_cost": str(unit_cost),
            "expiration_date": str(expiration_date),
        },
        role_targets=["staff", "cashier", "kitchen", "bar", "admin"],
    )
    return batch


@transaction.atomic
def consume_ingredient(*, ingredient: Ingredient, quantity: Decimal, actor=None, note=None, related_order_id=None):
    remaining = Decimal(quantity)
    if ingredient.available_quantity < remaining:
        raise ValidationError(f"Insufficient inventory for {ingredient.name}.")

    for batch in ingredient.batches.select_for_update().filter(quantity_remaining__gt=0).order_by("expiration_date", "created_at"):
        if remaining <= 0:
            break
        deduction = min(batch.quantity_remaining, remaining)
        batch.quantity_remaining -= deduction
        batch.save(update_fields=["quantity_remaining", "updated_at"])
        InventoryMovement.objects.create(
            ingredient=ingredient,
            batch=batch,
            movement_type=InventoryMovement.MOVEMENT_DEDUCT,
            quantity=deduction,
            actor=actor,
            note=note,
            related_order_id=related_order_id,
        )
        remaining -= deduction

    recalculate_menu_availability()
    publish_ingredient_stock_event(ingredient)


def ingredient_stock_projection():
    projections = defaultdict(dict)
    for ingredient in Ingredient.objects.all():
        projections[ingredient.id] = {
            "ingredient": ingredient.name,
            "available_quantity": ingredient.available_quantity,
            "reorder_level": ingredient.reorder_level,
            "is_low": ingredient.available_quantity <= ingredient.reorder_level,
        }
    return projections
