from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.audit_logs.services import log_user_action
from apps.inventory.models import Ingredient, InventoryBatch, InventoryMovement


def recalculate_menu_availability():
    from apps.menu.models import MenuItem

    for menu_item in MenuItem.objects.all():
        menu_item.recalculate_availability(save=True)


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
