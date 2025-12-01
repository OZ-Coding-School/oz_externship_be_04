from typing import Any

from django.test import Client
from django.urls import reverse


def test_mock_notification(client: Client) -> None:
    url = reverse("notification:notification-list")
    resp: Any = client.get(url)
    assert resp.status_code == 200
