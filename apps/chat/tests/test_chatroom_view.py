from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.chat.models.chat_message import ChatMessage
from apps.chat.models.last_read_message import LastReadMessage
from apps.study_groups.models import GroupMember, StudyGroup
from apps.users.models import User


class TestChatRoomViews(APITestCase):
    def setUp(self) -> None:
        # 인증 완료된 사용자
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

        self.anon_client = self.client_class()

        # 다른 유저(그룹 미참여)
        self.other_user = User.objects.create(
            email="hayeong@example.com",
            name="송하영",
            nickname="ha0",
            phone_number="01012341234",
            gender="F",
            birthday="1997-09-29",
        )

        # 스터디 그룹
        self.group = StudyGroup.objects.create(
            name="Django Study",
            introduction="스터디 소개",
            max_headcount=5,
            start_at="2025-12-01T00:00:00Z",
            end_at="2025-12-30T00:00:00Z",
        )

        # 그룹 멤버 등록
        GroupMember.objects.create(
            study_group_id=self.group,
            user_id=self.user,
        )

        # 메시지 생성
        self.msg1 = ChatMessage.objects.create(
            study_group=self.group,
            sender=self.user,
            content="msg1",
        )
        self.msg2 = ChatMessage.objects.create(
            study_group=self.group,
            sender=self.user,
            content="msg2",
        )

    # 채팅방 목록 조회 성공
    def test_chatroom_list_success(self) -> None:
        url = reverse("api_v1_chatrooms_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    # 채팅방 목록 조회 - 미인증 > 401
    def test_chatroom_list_unauthenticated(self) -> None:
        url = reverse("api_v1_chatrooms_list")
        response = self.anon_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 채팅방 상세 조회 성공
    def test_chatroom_detail_success(self) -> None:
        url = reverse("api_v1_chatrooms_retrieve", kwargs={"group_id": self.group.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.group.id)

    # 채팅방 상세 조회 - 존재하지 않음 > 404
    def test_chatroom_detail_not_found(self) -> None:
        url = reverse("api_v1_chatrooms_retrieve", kwargs={"group_id": 99999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 전체 읽음 처리 성공
    def test_mark_all_read_success(self) -> None:
        url = reverse("api_v1_chatrooms_mark_all_read", kwargs={"group_id": self.group.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        last_read = LastReadMessage.objects.get(study_group=self.group, user=self.user)
        self.assertEqual(last_read.message.id, self.msg2.id)

    # 전체 읽음 처리 - 미참여자 > 403
    def test_mark_all_read_not_member(self) -> None:
        self.client.force_authenticate(self.other_user)

        url = reverse("api_v1_chatrooms_mark_all_read", kwargs={"group_id": self.group.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
