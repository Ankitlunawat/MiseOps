"""Verify persistence, constraints and locking on a real PostgreSQL database."""
import base64
import json
from unittest import skipUnless
from django.contrib.auth import get_user_model
from django.db import connection, transaction, IntegrityError, connections
from django.test import TransactionTestCase, Client
from django.utils.timezone import now
from .models import WorkOrder

@skipUnless(connection.vendor == 'postgresql', 'Requires PostgreSQL')
class PostgreSQLTests(TransactionTestCase):
    def setUp(self):
        get_user_model().objects.create_user('manager', password='test-only-password', is_staff=True)
        self.headers = {'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode(b'manager:test-only-password').decode()}
        self.order = WorkOrder.objects.create(title='Prep', station='Kitchen', assignee='Chef', quantity=20, due=now())

    def test_server_reports_postgresql_and_persists(self):
        with connection.cursor() as cursor:
            cursor.execute('SELECT version()')
            self.assertIn('PostgreSQL', cursor.fetchone()[0])
        connection.close()
        self.assertEqual(WorkOrder.objects.get(pk=self.order.pk).quantity, 20)

    def test_database_rejects_zero_quantity(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WorkOrder.objects.filter(pk=self.order.pk).update(quantity=0)

    def test_concurrent_transition_applies_once(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        barrier = Barrier(2)
        def transition():
            try:
                barrier.wait(timeout=10)
                return Client().post(f'/api/orders/{self.order.pk}/transition/', json.dumps({'status':'preparing'}), content_type='application/json', **self.headers).status_code
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: transition(), range(2)))
        self.assertEqual(sorted(results), [200, 409])
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'preparing')
        self.assertEqual(self.order.activity.count(), 1)
