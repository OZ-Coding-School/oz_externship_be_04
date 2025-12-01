from typing import Any
from django.test import TestCase, Client
from django.urls import reverse

class NotificationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_mock_notification(self) -> None:
        url = reverse("notification:notification-list")
        resp: Any = self.client.get(url)
        assert resp.resolver_match.view_name == "notification:notification-list"
        assert resp.status_code == 200
