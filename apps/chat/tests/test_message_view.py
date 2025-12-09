from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.chat.models.chat_message import ChatMessage
from apps.study_groups.models import GroupMember, StudyGroup
from apps.users.models import User


class TestMessageViews(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(
            email="test@example.com",
            name="김오즈",
            nickname="테스터",
            phone_number="01012345678",
            gender="M",
            birthday="1999-01-01",
            password="qwer1234",
        )
        self.client.force_authenticate(self.user)

        self.other_user = User.objects.create(
            email="hayeong@example.com",
            name="송하영",
            nickname="ha0",
            phone_number="01012341234",
            gender="F",
            birthday="1997-09-29",
            password="pass1234",
        )

        self.group = StudyGroup.objects.create(
            name="Django Study",
            introduction="스터디 소개",
            max_headcount=5,
            start_at="2025-12-01T00:00:00Z",
            end_at="2025-12-30T00:00:00Z",
        )

        GroupMember.objects.create(
            study_group_id=self.group,
            user_id=self.user,
        )

        self.msg = ChatMessage.objects.create(
            study_group=self.group,
            sender=self.user,
            content="hello test",
        )

    # 메시지 목록 조회 성공
    def test_message_list(self) -> None:
        url = reverse("api_v1_chatroom_message_list", kwargs={"group_id": self.group.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    # 메시지 목록 조회 - 미참여자 > 403
    def test_message_list_not_member(self) -> None:
        self.client.force_authenticate(self.other_user)

        url = reverse("api_v1_chatroom_message_list", kwargs={"group_id": self.group.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 메시지 생성 성공
    def test_message_create_success(self) -> None:
        url = reverse("api_v1_chatroom_message_create", kwargs={"group_id": self.group.id})

        response = self.client.post(url, {"content": "새 메시지"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], "새 메시지")

    # 메시지 생성 - 빈 내용 > 400
    def test_message_create_empty_content(self) -> None:
        url = reverse("api_v1_chatroom_message_create", kwargs={"group_id": self.group.id})

        response = self.client.post(url, {"content": "   "}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 단일 메시지 조회 성공
    def test_message_detail(self) -> None:
        url = reverse("api_v1_messages_retrieve", kwargs={"message_id": self.msg.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # 단일 메시지 조회 - 존재 X > 404
    def test_message_detail_not_found(self) -> None:
        url = reverse("api_v1_messages_retrieve", kwargs={"message_id": 999999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
