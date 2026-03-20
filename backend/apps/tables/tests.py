from django.test import TestCase

from apps.tables.models import Table


class TableTests(TestCase):
    def test_table_generates_qr_code_value(self):
        table = Table.objects.create(identifier="A1", capacity=4)
        self.assertTrue(table.qr_code_value.startswith("TABLEQR-"))
