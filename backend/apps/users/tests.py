from django.test import TestCase
from rest_framework.test import APIClient

from apps.users.models import User


class UserModelTests(TestCase):
    def test_user_requires_email_or_phone(self):
        with self.assertRaises(Exception):
            User.objects.create_user(password="password123")

    def test_staff_requires_staff_role(self):
        with self.assertRaises(Exception):
            User.objects.create_user(email="staff@example.com", password="password123", role="staff")


class GuestIdentityApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_guest_start_issues_guest_key_and_expiry(self):
        response = self.client.post("/api/identity/guest/start/", {"guest_name": "Walk In"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("guest_key", response.data)
        self.assertIn("guest_user_id", response.data)
        self.assertIn("expires_at", response.data)
        guest = User.objects.get(id=response.data["guest_user_id"])
        self.assertTrue(guest.is_guest)
