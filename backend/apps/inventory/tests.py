from decimal import Decimal
from datetime import date, timedelta

from django.test import TestCase

from apps.inventory.models import Ingredient
from apps.inventory.services import restock_batch
from apps.menu.models import Category, MenuItem, MenuItemIngredient
from apps.users.models import User


class InventoryAvailabilityTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(email="kitchen@example.com", password="password123", role="staff", staff_role="kitchen")
        self.category = Category.objects.create(name="Desserts")
        self.sugar = Ingredient.objects.create(name="Sugar", unit="g", reorder_level=Decimal("2"))
        self.cake = MenuItem.objects.create(name="Cake", category=self.category, price=100, prep_eta_minutes=10)
        self.tea = MenuItem.objects.create(name="Tea", category=self.category, price=80, prep_eta_minutes=5)
        MenuItemIngredient.objects.create(menu_item=self.cake, ingredient=self.sugar, quantity_required=Decimal("5"))
        MenuItemIngredient.objects.create(menu_item=self.tea, ingredient=self.sugar, quantity_required=Decimal("3"))

    def test_menu_item_availability_uses_required_ingredient_quantity(self):
        restock_batch(
            ingredient=self.sugar,
            quantity=Decimal("4"),
            unit_cost=Decimal("1"),
            expiration_date=date.today() + timedelta(days=30),
            actor=self.staff,
        )
        self.cake.refresh_from_db()
        self.tea.refresh_from_db()
        self.assertFalse(self.cake.is_available)
        self.assertTrue(self.tea.is_available)
