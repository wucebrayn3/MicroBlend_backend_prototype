from django.contrib import admin
from django import forms
from django.db import models

from .models import Ingredient, InventoryBatch, InventoryMovement


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "reorder_level", "available_quantity")
    search_fields = ("name",)


@admin.register(InventoryBatch)
class InventoryBatchAdmin(admin.ModelAdmin):
    list_display = ("ingredient", "quantity_added", "quantity_remaining", "unit_cost", "expiration_date", "source", "created_at")
    list_filter = ("ingredient", "expiration_date")
    search_fields = ("ingredient__name", "source")
    exclude = ("quantity_remaining",)
    readonly_fields = ("created_at", "updated_at")
    formfield_overrides = {
        models.DateField: {"widget": forms.DateInput(attrs={"type": "date"})},
    }

    def save_model(self, request, obj, form, change):
        if not change and not obj.quantity_remaining:
            obj.quantity_remaining = obj.quantity_added
        super().save_model(request, obj, form, change)


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ("ingredient", "movement_type", "quantity", "actor", "created_at")
    list_filter = ("movement_type", "ingredient")
    search_fields = ("ingredient__name", "note")
