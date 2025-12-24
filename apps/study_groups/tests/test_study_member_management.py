from datetime import date, timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.lectures.models import CrawledLecture
from apps.study_groups.models import GroupMember, StudyGroup

UserModel = get_user_model()


# 스터디그룹 멤버 관리
class StudyGroupMemberManagementTests(TestCase):
    def setUp(self) -> None:
        self.leader = UserModel.objects.create(
            nickname="leader",
            email="leader@example.com",
            name="리더",
            birthday=date(2000, 1, 1),
            phone_number="01000000001",
            gender="M",
        )
        self.leader.set_password("qwer1234")
        self.leader.save()

        self.member1 = UserModel.objects.create(
            nickname="member1",
            email="member1@example.com",
            name="멤버1",
            birthday=date(2000, 1, 1),
            phone_number="01000000002",
            gender="M",
        )
        self.member1.set_password("qwer1234")
        self.member1.save()

        self.member2 = UserModel.objects.create(
            nickname="member2",
            email="member2@example.com",
            name="멤버2",
            birthday=date(2000, 1, 1),
            phone_number="01000000003",
            gender="M",
        )
        self.member2.set_password("qwer1234")
        self.member2.save()

        # 테스트용 강의 생성
        self.lecture1 = CrawledLecture.objects.create(
            title="강의1",
            instructor="강사1",
            external_id="1",
            average_rating=0.0,
            total_class_time=0,
            difficulty="EASY",
            description="테스트 강의1",
            platform="INFLEARN",
            url_link="https://example.com/lecture1",
            thumbnail_img_url="https://example.com/thumb1.jpg",
        )
        self.lecture2 = CrawledLecture.objects.create(
            title="강의2",
            instructor="강사2",
            external_id="2",
            average_rating=0.0,
            total_class_time=0,
            difficulty="EASY",
            description="테스트 강의2",
            platform="INFLEARN",
            url_link="https://example.com/lecture2",
            thumbnail_img_url="https://example.com/thumb2.jpg",
        )

        self.study_group = StudyGroup.objects.create(
            name="테스트 스터디",
            max_headcount=5,
            start_at=now() + timedelta(days=1),
            end_at=now() + timedelta(days=10),
        )

        GroupMember.objects.create(
            study_group_id=self.study_group,
            user_id=self.leader,
            is_leader=True,
        )
        GroupMember.objects.create(
            study_group_id=self.study_group,
            user_id=self.member1,
            is_leader=False,
        )
        GroupMember.objects.create(
            study_group_id=self.study_group,
            user_id=self.member2,
            is_leader=False,
        )

        self.leader_client: Any = APIClient()
        self.leader_client.force_authenticate(user=self.leader)

        self.member_client: Any = APIClient()
        self.member_client.force_authenticate(user=self.member1)

    # 리더 위임
    def test_delegate_leader_success(self) -> None:
        url = reverse("delegate-leader", args=[self.study_group.id])
        # GroupMember ID를 전달
        member1_group_member = GroupMember.objects.get(study_group_id=self.study_group, user_id=self.member1.id)
        data = {"target_member_id": member1_group_member.id}

        response: Response = self.leader_client.post(url, data, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("리더 권한이 위임되었습니다", response.data["detail"])

        # 리더 권한 변경
        self.assertFalse(
            GroupMember.objects.filter(
                study_group_id=self.study_group.id,
                user_id=self.leader.id,
                is_leader=True,
            ).exists()
        )
        self.assertTrue(
            GroupMember.objects.filter(
                study_group_id=self.study_group.id,
                user_id=self.member1.id,
                is_leader=True,
            ).exists()
        )

    # 일반 멤버가 리더 위임
    def test_delegate_leader_permission_denied(self) -> None:
        url = reverse("delegate-leader", args=[self.study_group.id])
        # GroupMember ID를 전달
        member2_group_member = GroupMember.objects.get(study_group_id=self.study_group, user_id=self.member2.id)
        data = {"target_member_id": member2_group_member.id}

        response: Response = self.member_client.post(url, data, format="json")

        self.assertEqual(response.status_code, 403)
        self.assertIn("리더만 권한을 위임할 수 있습니다", response.data["error_detail"])

    # 존재하지 않는 멤버
    def test_delegate_leader_member_not_found(self) -> None:
        url = reverse("delegate-leader", args=[self.study_group.id])
        data = {"target_member_id": 99999}

        response: Response = self.leader_client.post(url, data, format="json")

        self.assertEqual(response.status_code, 404)
        self.assertIn("해당 멤버를 찾을 수 없습니다", response.data["error_detail"])

    # 이미 리더인 멤버(자기자신)
    def test_delegate_leader_to_leader(self) -> None:
        url = reverse("delegate-leader", args=[self.study_group.id])
        # 리더의 GroupMember ID를 전달
        leader_group_member = GroupMember.objects.get(study_group_id=self.study_group, user_id=self.leader.id)
        data = {"target_member_id": leader_group_member.id}

        response: Response = self.leader_client.post(url, data, format="json")

        self.assertEqual(response.status_code, 404)
        self.assertIn("이미 리더인 멤버입니다", response.data["error_detail"])

    # 리더가 멤버 추방
    def test_kick_member_success(self) -> None:
        # GroupMember ID를 전달
        member1_group_member = GroupMember.objects.get(study_group_id=self.study_group, user_id=self.member1.id)
        url = reverse("study-group-kick", args=[self.study_group.id, member1_group_member.id])

        response: Response = self.leader_client.delete(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("멤버를 추방하는데 성공했습니다", response.data["detail"])
        self.assertFalse(
            GroupMember.objects.filter(
                study_group_id=self.study_group.id,
                user_id=self.member1.id,
            ).exists()
        )

    # 일반 멤버가 멤버 추방
    def test_kick_member_permission_denied(self) -> None:
        # GroupMember ID를 전달
        member2_group_member = GroupMember.objects.get(study_group_id=self.study_group, user_id=self.member2.id)
        url = reverse("study-group-kick", args=[self.study_group.id, member2_group_member.id])

        response: Response = self.member_client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertIn("리더만 멤버를 추방할 수 있습니다", response.data["error_detail"])

    def test_kick_leader_forbidden(self) -> None:
        # 리더 추방 - GroupMember ID를 전달
        leader_group_member = GroupMember.objects.get(study_group_id=self.study_group, user_id=self.leader.id)
        url = reverse("study-group-kick", args=[self.study_group.id, leader_group_member.id])

        response: Response = self.leader_client.delete(url)

        self.assertEqual(response.status_code, 404)
        self.assertIn("리더는 추방할 수 없습니다", response.data["error_detail"])

    # 존재하지 않는 멤버 추방
    def test_kick_member_not_found(self) -> None:
        url = reverse("study-group-kick", args=[self.study_group.id, 99999])

        response: Response = self.leader_client.delete(url)

        self.assertEqual(response.status_code, 404)
        self.assertIn("해당 멤버를 찾을 수 없습니다", response.data["error_detail"])

    # 스터디그룹 나가기
    def test_leave_study_group_success(self) -> None:
        url = reverse("study-group-leave", args=[self.study_group.id])

        response: Response = self.member_client.delete(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("나가기에 성공했습니다", response.data["detail"])
        self.assertFalse(
            GroupMember.objects.filter(
                study_group_id=self.study_group.id,
                user_id=self.member1.id,
            ).exists()
        )

    # 리더 스터디그룹 탈퇴
    def test_leave_study_group_as_leader_forbidden(self) -> None:
        url = reverse("study-group-leave", args=[self.study_group.id])

        response: Response = self.leader_client.delete(url)

        self.assertEqual(response.status_code, 400)
        self.assertIn("리더는 스터디 그룹을 나갈 수 없습니다", response.data["error_detail"])

    # 멤버가 아닌 사용자
    def test_leave_study_group_not_member(self) -> None:
        non_member = UserModel.objects.create(
            nickname="non_member",
            email="non_member@example.com",
            birthday=date(2000, 1, 1),
            phone_number="01000000004",
        )
        non_member_client: Any = APIClient()
        non_member_client.force_authenticate(user=non_member)

        url = reverse("study-group-leave", args=[self.study_group.id])

        response: Response = non_member_client.delete(url)

        self.assertEqual(response.status_code, 400)
        self.assertIn("스터디 그룹에 속해있지 않습니다", response.data["error_detail"])
