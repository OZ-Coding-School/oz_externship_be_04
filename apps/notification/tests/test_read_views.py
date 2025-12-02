from apps.users.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from apps.notification.models import Notification




class NotificationReadAPITestCase(APITestCase):
    user: User
    notification: Notification
    notification_read: Notification
    notification_unread: Notification

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create(
            email="test@example.com",
            password="testpassword123",
            nickname="testuser",
            name="테스트유저",
            phone_number="01012345678",
            birthday="2000-12-31",
            gender="M",
        )


    # 로그인 처리
    def setUp(self) -> None:
        self.client.force_authenticate(user=self.user)

        self.notification_unread = Notification.objects.create(
            user=self.user,
            content="읽지 않은 알림",
            is_read=False,
            back_url_link= ""
        )
        self.notification_read = Notification.objects.create(
            user=self.user,
            content="읽음 처리된 알림",
            is_read=True,
            back_url_link=""
        )

    # 읽지 않은 알림을 읽음 처리할 때 is_read=Ture로 처리
    def test_mark_notification_read(self) -> None:
        url = reverse("notification:notification-read", kwargs={"notification_id": self.notification_unread.id})
        response: Response = self.client.post(url)
        self.notification_unread.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.notification_unread.is_read)
        self.assertEqual(response.data["detail"], "알림 읽음처리에 성공하였습니다.")

    # 이미 읽은 알림에 다시 POST 요청하면 200 OK, 상태는 유지
    def test_mark_notification_already_read(self) -> None:
        url = reverse("notification:notification-read", kwargs={"notification_id": self.notification_read.id})
        response: Response = self.client.post(url)
        self.notification_read.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.notification_read.is_read)
        self.assertEqual(response.data["detail"], "알림 읽음처리에 성공하였습니다.")

    # 존재하지 않는 알림 id로 요청시 404
    def test_mark_notification_not_found(self) -> None:
        url = reverse("notification:notification-read", kwargs={"notification_id": 9999999})
        response: Response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "해당 알림 내역을 찾을 수 없습니다.")

    # 읽지 않은 모든 알림을 한 번에 읽음 처리
    def test_mark_all_notifications_as_read(self) -> None:

        url = reverse("notification:notification-read-all")
        response: Response = self.client.post(url)

        unread_count = Notification.objects.filter(user=self.user, is_read=False).count()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("알림 읽음처리에 성공하였습니다.", response.data["detail"])
        self.assertEqual(unread_count, 0)

# todo 로그인 된 유저만 알림 확인 할 수 있는 테스트 추가 하기