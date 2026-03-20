from django.test import TestCase

from apps.analytics.services import build_dashboard_snapshot
from common.utils import get_date_range


class AnalyticsTests(TestCase):
    def test_dashboard_snapshot_returns_expected_keys(self):
        start_at, end_at = get_date_range("daily")
        snapshot = build_dashboard_snapshot(start_at, end_at)
        self.assertIn("revenue", snapshot)
        self.assertIn("order_count", snapshot)
