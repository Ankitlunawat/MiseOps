import base64
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import WorkOrder

class WorkflowTests(TestCase):
    def setUp(self):
        get_user_model().objects.create_user('chef', password='test-only-password', is_staff=True)
        self.headers = {'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode(b'chef:test-only-password').decode()}
        self.data = {'title': 'Lunch prep', 'station': 'Hot kitchen', 'assignee': 'Chef', 'quantity': 24, 'due': '2026-10-16T12:00:00+05:30'}
    def post(self, url, data):
        return self.client.post(url, json.dumps(data), content_type='application/json', **self.headers)
    def test_authentication_required(self):
        self.assertEqual(self.client.get('/api/orders/').status_code, 401)
    def test_invalid_quantity_rejected(self):
        self.assertEqual(self.post('/api/orders/', {**self.data, 'quantity': 0}).status_code, 400)
        self.assertEqual(WorkOrder.objects.count(), 0)
    def test_workflow_and_audit(self):
        response = self.post('/api/orders/', self.data)
        self.assertEqual(response.status_code, 201)
        url = f"/api/orders/{response.json()['id']}/transition/"
        self.assertEqual(self.post(url, {'status': 'closed'}).status_code, 409)
        for status in ('preparing', 'ready', 'closed'):
            self.assertEqual(self.post(url, {'status': status}).status_code, 200)
        self.assertEqual(WorkOrder.objects.get().activity.count(), 4)
        self.assertEqual(self.post(url, {'status': 'queued'}).status_code, 409)
    def test_staff_scope_and_export(self):
        user = get_user_model().objects.get(username='chef'); user.is_staff = False; user.save()
        self.assertEqual(self.client.get('/api/orders/', **self.headers).status_code, 401)
        user.is_staff = True; user.save()
        self.post('/api/orders/', {**self.data, 'title': '=formula'})
        output = self.client.get('/api/export/', **self.headers)
        self.assertIn("'=formula", output.content.decode())
