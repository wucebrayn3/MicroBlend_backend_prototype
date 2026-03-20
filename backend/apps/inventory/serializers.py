from rest_framework import serializers

from apps.inventory.models import Ingredient, InventoryBatch, InventoryMovement
from apps.inventory.services import restock_batch


class IngredientSerializer(serializers.ModelSerializer):
    available_quantity = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Ingredient
        fields = ("id", "name", "unit", "reorder_level", "available_quantity", "created_at", "updated_at")


class InventoryBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryBatch
        fields = "__all__"
        read_only_fields = ("quantity_remaining",)

    def create(self, validated_data):
        actor = self.context["request"].user if self.context.get("request") else None
        return restock_batch(actor=actor, **validated_data)


class InventoryMovementSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)

    class Meta:
        model = InventoryMovement
        fields = "__all__"
        read_only_fields = (
            "id",
            "ingredient",
            "batch",
            "movement_type",
            "quantity",
            "actor",
            "note",
            "related_order_id",
            "created_at",
            "updated_at",
            "ingredient_name",
        )
