from django.test import TestCase

from apps.menu.models import Category, MenuItem


class MenuOrderingTests(TestCase):
    def test_category_and_menu_item_can_be_created(self):
        category = Category.objects.create(name="Beverages")
        item = MenuItem.objects.create(name="Iced Tea", category=category, price=75, prep_eta_minutes=5)
        self.assertEqual(item.category.name, "Beverages")
