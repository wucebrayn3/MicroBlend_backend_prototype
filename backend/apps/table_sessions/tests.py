from django.test import TestCase

from apps.tables.models import Table
from apps.table_sessions.models import TableSession


class TableSessionTests(TestCase):
    def test_session_creation_sets_table_reference(self):
        table = Table.objects.create(identifier="B1", capacity=2)
        session = TableSession.objects.create(table=table, source="manual", party_size=2)
        self.assertEqual(session.table.identifier, "B1")
