from decimal import Decimal

from django.conf import settings
from django.db import models

from common.constants import PREPARATION_STATION_CHOICES, STATION_KITCHEN
from common.models import BaseModel


class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "name")

    def __str__(self):
        return self.name


class MenuItem(BaseModel):
    name = models.CharField(max_length=200, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="items")
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    prep_eta_minutes = models.PositiveIntegerField(default=10)
    preparation_station = models.CharField(
        max_length=20,
        choices=PREPARATION_STATION_CHOICES,
        default=STATION_KITCHEN,
    )
    is_available = models.BooleanField(default=True)
    popularity_score = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("name",)

    def recalculate_availability(self, save=False):
        ingredient_requirements = self.ingredients.select_related("ingredient")
        is_available = True
        for requirement in ingredient_requirements:
            if requirement.ingredient.available_quantity < requirement.quantity_required:
                is_available = False
                break
        self.is_available = is_available
        if save:
            self.save(update_fields=["is_available", "updated_at"])
        return is_available

    def increase_popularity(self, quantity=1):
        self.popularity_score += quantity
        self.save(update_fields=["popularity_score", "updated_at"])

    def __str__(self):
        return self.name


class MenuItemIngredient(BaseModel):
    menu_item = models.ForeignKey(MenuItem, related_name="ingredients", on_delete=models.CASCADE)
    ingredient = models.ForeignKey("inventory.Ingredient", related_name="menu_links", on_delete=models.CASCADE)
    quantity_required = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1"))

    class Meta:
        unique_together = ("menu_item", "ingredient")

    def __str__(self):
        return f"{self.menu_item.name} -> {self.ingredient.name}"


class OrderPlaylist(BaseModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="order_playlists", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)

    class Meta:
        unique_together = ("owner", "name")
        ordering = ("name",)

    def __str__(self):
        return self.name


class OrderPlaylistItem(BaseModel):
    playlist = models.ForeignKey(OrderPlaylist, related_name="items", on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("playlist", "menu_item")

    def __str__(self):
        return f"{self.playlist.name}: {self.menu_item.name}"
