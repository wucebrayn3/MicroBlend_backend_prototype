from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.notifications.services import enforce_debounce


class DebounceTests(TestCase):
    def test_enforce_debounce_blocks_immediate_duplicate_action(self):
        enforce_debounce(actor_key="user:1", action="order.submit", window_seconds=30, object_key="table:1")
        with self.assertRaises(ValidationError):
            enforce_debounce(actor_key="user:1", action="order.submit", window_seconds=30, object_key="table:1")
