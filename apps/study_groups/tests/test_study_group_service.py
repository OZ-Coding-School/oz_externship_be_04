from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.study_groups.models import GroupMember, StudyGroup
from apps.study_groups.services.study_group_service import (
    create_study_group,
    delegate_leader,
    get_study_group_list,
    kick_member,
    leave_study_group,
)
from apps.users.models import User


class StudyGroupServiceTest(TestCase):
    def setUp(self) -> None:
        self.leader = User.objects.create_user(
            email="l@example.com",
            password="1234",
            name="l",
            nickname="l",
            phone_number="01000000000",
            gender="M",
            birthday=timezone.now().date(),
            profile_img_url="https://x.com/l.png",
        )
        self.member = User.objects.create_user(
            email="m@example.com",
            password="1234",
            name="m",
            nickname="m",
            phone_number="01000000001",
            gender="F",
            birthday=timezone.now().date(),
            profile_img_url="https://x.com/m.png",
        )
        self.group = StudyGroup.objects.create(
            name="svc",
            introduction="i",
            max_headcount=3,
            profile_img_url="https://x.com/g.png",
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=7),
        )
        self.leader_member = GroupMember.objects.create(study_group_id=self.group, user_id=self.leader, is_leader=True)
        self.normal_member = GroupMember.objects.create(study_group_id=self.group, user_id=self.member, is_leader=False)

    def test_delegate_leader_swaps_flags(self) -> None:
        delegate_leader(self.leader_member, self.normal_member)

        self.leader_member.refresh_from_db()
        self.normal_member.refresh_from_db()
        self.assertFalse(self.leader_member.is_leader)
        self.assertTrue(self.normal_member.is_leader)

    def test_leave_study_group_blocks_leader(self) -> None:
        with self.assertRaises(ValueError):
            leave_study_group(self.leader_member)

    def test_leave_study_group_allows_member(self) -> None:
        leave_study_group(self.normal_member)
        self.assertFalse(GroupMember.objects.filter(id=self.normal_member.id).exists())

    def test_kick_member_requires_leader(self) -> None:
        with self.assertRaises(PermissionError):
            kick_member(self.normal_member, self.leader_member)

    def test_kick_member_blocks_kicking_leader(self) -> None:
        with self.assertRaises(ValueError):
            kick_member(self.leader_member, self.leader_member)

    def test_kick_member_success(self) -> None:
        kick_member(self.leader_member, self.normal_member)
        self.assertFalse(GroupMember.objects.filter(id=self.normal_member.id).exists())

    def test_create_and_list_study_group(self) -> None:
        payload = {
            "name": "svc-create",
            "introduction": "i",
            "max_headcount": 3,
            "profile_img_url": "https://x.com/g.png",
            "start_at": timezone.now(),
            "end_at": timezone.now() + timedelta(days=7),
        }
        group = create_study_group(self.leader, payload)
        self.assertTrue(GroupMember.objects.filter(study_group_id=group, user_id=self.leader, is_leader=True).exists())

        qs = get_study_group_list(status=None)
        self.assertTrue(qs.filter(id=group.id).exists())
