from decimal import Decimal
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.inventory.models import Ingredient
from apps.inventory.services import restock_batch
from apps.menu.models import Category, MenuItem, MenuItemIngredient
from apps.orders.services import cancel_order, create_or_update_draft_order, set_station_status, submit_order
from apps.table_sessions.models import TableSession
from apps.tables.models import Table
from apps.users.models import User


class OrderLifecycleTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(email="customer@example.com", password="password123")
        self.kitchen = User.objects.create_user(email="kitchen@example.com", password="password123", role="staff", staff_role="kitchen")
        self.category = Category.objects.create(name="Meals")
        self.ingredient = Ingredient.objects.create(name="Rice", unit="g", reorder_level=Decimal("5"))
        self.menu_item = MenuItem.objects.create(name="Rice Meal", category=self.category, price=120, prep_eta_minutes=15)
        MenuItemIngredient.objects.create(menu_item=self.menu_item, ingredient=self.ingredient, quantity_required=Decimal("5"))
        restock_batch(
            ingredient=self.ingredient,
            quantity=Decimal("100"),
            unit_cost=Decimal("1"),
            expiration_date=date.today() + timedelta(days=30),
            actor=self.kitchen,
        )
        self.table = Table.objects.create(identifier="C1", capacity=4)
        self.session = TableSession.objects.create(table=self.table, customer_account=self.customer, source="manual", party_size=2)

    def test_order_can_be_cancelled_before_station_preparation(self):
        order = create_or_update_draft_order(
            actor=self.customer,
            order=None,
            order_data={"table_session": self.session},
            items_data=[{"menu_item": self.menu_item, "quantity": 2}],
        )
        submit_order(order, actor=self.customer)
        cancel_order(order, actor=self.customer)
        order.refresh_from_db()
        self.assertEqual(order.status, "cancelled")

    def test_order_cannot_be_cancelled_after_kitchen_starts(self):
        order = create_or_update_draft_order(
            actor=self.customer,
            order=None,
            order_data={"table_session": self.session},
            items_data=[{"menu_item": self.menu_item, "quantity": 1}],
        )
        submit_order(order, actor=self.customer)
        set_station_status(order=order, station="kitchen", status_value="preparing", actor=self.kitchen)
        with self.assertRaises(ValidationError):
            cancel_order(order, actor=self.customer)
