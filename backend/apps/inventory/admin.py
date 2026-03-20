from django.contrib import admin

from .models import Ingredient, InventoryBatch, InventoryMovement

admin.site.register(Ingredient)
admin.site.register(InventoryBatch)
admin.site.register(InventoryMovement)
