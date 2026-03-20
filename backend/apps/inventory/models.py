from decimal import Decimal

from django.conf import settings
from django.db import models

from common.models import BaseModel


class Ingredient(BaseModel):
    UNIT_GRAM = "g"
    UNIT_MILLILITER = "ml"
    UNIT_PIECE = "pc"

    UNIT_CHOICES = (
        (UNIT_GRAM, "Gram"),
        (UNIT_MILLILITER, "Milliliter"),
        (UNIT_PIECE, "Piece"),
    )

    name = models.CharField(max_length=150, unique=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default=UNIT_GRAM)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))

    class Meta:
        ordering = ("name",)

    @property
    def available_quantity(self):
        result = self.batches.aggregate(total=models.Sum("quantity_remaining"))["total"]
        return result or Decimal("0")

    def __str__(self):
        return self.name


class InventoryBatch(BaseModel):
    ingredient = models.ForeignKey(Ingredient, related_name="batches", on_delete=models.CASCADE)
    quantity_added = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_remaining = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    expiration_date = models.DateField()
    source = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        ordering = ("expiration_date", "created_at")

    def __str__(self):
        return f"{self.ingredient.name} batch {self.id}"


class InventoryMovement(BaseModel):
    MOVEMENT_RESTOCK = "restock"
    MOVEMENT_DEDUCT = "deduct"
    MOVEMENT_ADJUST = "adjust"
    MOVEMENT_DELETE = "delete"

    MOVEMENT_CHOICES = (
        (MOVEMENT_RESTOCK, "Restock"),
        (MOVEMENT_DEDUCT, "Deduct"),
        (MOVEMENT_ADJUST, "Adjust"),
        (MOVEMENT_DELETE, "Delete"),
    )

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="movements")
    batch = models.ForeignKey(InventoryBatch, on_delete=models.SET_NULL, null=True, blank=True)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.CharField(max_length=255, blank=True, null=True)
    related_order_id = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.ingredient.name} {self.movement_type} {self.quantity}"
