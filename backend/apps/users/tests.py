from django.test import TestCase

from apps.users.models import User


class UserModelTests(TestCase):
    def test_user_requires_email_or_phone(self):
        with self.assertRaises(Exception):
            User.objects.create_user(password="password123")

    def test_staff_requires_staff_role(self):
        with self.assertRaises(Exception):
            User.objects.create_user(email="staff@example.com", password="password123", role="staff")
