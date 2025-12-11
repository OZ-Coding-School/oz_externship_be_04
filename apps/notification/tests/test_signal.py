from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.application.models import Application, ApplicationStatus
from apps.notification.models import Notification, notification
from apps.recruitment.models import Recruitment
from apps.study_groups.models import GroupMember, StudyGroup, StudyNote
from apps.users.models.users import GenderChoices, User


class SignalTestCase(TestCase):
    def setUp(self) -> None:
        self.author = User.objects.create(
            email="author@test.com",
            nickname="author",
            name="author",
            password="password123",
            phone_number="010-1234-5679",
            gender=GenderChoices.MALE,
            birthday=date(1995, 1, 11),
        )
        self.applicant = User.objects.create(
            email="applicant_{unique_id}@test.com",
            nickname="applicant",
            name="applicant",
            password="password123",
            phone_number="010-1234-5609",
            gender=GenderChoices.MALE,
            birthday=date(1995, 1, 12),
        )

        self.existing_member = User.objects.create(
            email="existing@test.com",
            nickname="existing",
            name="existing",
            password="password123",
            phone_number="010-1234-5890",
            gender=GenderChoices.MALE,
            birthday=date(1995, 1, 11),
        )

        self.study_group = StudyGroup.objects.create(
            name="오즈코딩스쿨",
            introduction="장고 익스턴십",
            max_headcount=5,
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc),
        )

        self.recruitment = Recruitment.objects.create(
            title="합동 프로젝트 모집",
            author=self.author,
            content="테스트 공고",
            estimated_fee=100400,
            expected_headcount=8,
            study_group=self.study_group,
        )
        GroupMember.objects.create(
            study_group_id=self.study_group,
            user_id=self.existing_member,
            is_leader=True,
        )

        GroupMember.objects.create(
            study_group_id=self.study_group,
            user_id=self.author,
            is_leader=False,
        )

    @patch("apps.notification.infra.task.send_to_pubsub.delay")
    def test_recruitment_created(self, mock_test: MagicMock) -> None:
        """공고 지원 알림 테스트"""
        application = Application.objects.create(
            recruitment=self.recruitment,
            applicant=self.applicant,
            self_introduction="자기소개",
            motivation="지원동기",
            objective="지원 목표",
            available_time="시간",
        )
        notification = Notification.objects.get(user=self.author, type=Notification.NotificationType.ADD_APPLICATION)

        self.assertEqual(notification.content, f"공고:'{self.recruitment.title}'에 새로운 지원자가 지원했습니다.")
        mock_test.assert_called_once_with(notification.id)

    @patch("apps.notification.infra.task.send_to_pubsub.delay")
    def test_recruitment_approved_created(self, mock_task: MagicMock) -> None:
        """공고 지원 승인 알림 테스트"""
        application = Application.objects.create(
            recruitment=self.recruitment,
            applicant=self.applicant,
            self_introduction="자기소개",
            motivation="지원동기",
            objective="지원 목표",
            available_time="시간",
        )
        application.status = ApplicationStatus.ACCEPTED
        application.save()

        notification = Notification.objects.get(
            user=self.applicant, type=Notification.NotificationType.APPLICATION_ACCEPT
        )

        self.assertEqual(notification.content, f"'{self.recruitment.title}'구인 공고에 대한 지원내역이 승인되었습니다.")
        self.assertEqual(mock_task.call_count, 4)

    @patch("apps.notification.infra.task.send_to_pubsub.delay")
    def test_recruitment_rejected_created(self, mock_task: MagicMock) -> None:
        """공고 지원 거절 알림 테스트"""
        application = Application.objects.create(
            recruitment=self.recruitment,
            applicant=self.applicant,
            self_introduction="자기소개",
            motivation="지원동기",
            objective="지원 목표",
            available_time="시간",
        )
        application.status = ApplicationStatus.REJECTED
        application.save()

        notification = Notification.objects.get(
            user=self.applicant, type=Notification.NotificationType.APPLICATION_REJECT
        )

        self.assertEqual(notification.content, f"'{self.recruitment.title}'구인 공고에 대한 지원내역이 거절되었습니다.")
        self.assertEqual(mock_task.call_count, 2)

    @patch("apps.notification.infra.task.send_to_pubsub.delay")
    def test_study_member_joined_created(self, mock_delay: MagicMock) -> None:
        """스터디 그룹 참여 알림 테스트"""
        self.recruitment.study_group = self.study_group
        self.recruitment.save()

        application = Application.objects.create(
            recruitment=self.recruitment,
            applicant=self.applicant,
            self_introduction="자기소개",
            motivation="지원동기",
            objective="지원 목표",
            available_time="시간",
        )

        application.status = ApplicationStatus.ACCEPTED
        application.save()

        notification = Notification.objects.get(
            user=self.existing_member, type=Notification.NotificationType.STUDY_JOIN
        )

        expected_content = f"{self.study_group.name}에 {self.applicant.nickname}님이 참여했습니다. 환영해주세요!"
        self.assertEqual(notification.content, expected_content)
        self.assertIn(str(self.study_group.id), notification.back_url_link)  # ✨ .id를 사용합니다.

        assert notification.back_url_link is not None

        self.assertEqual(mock_delay.call_count, 4)
        mock_delay.assert_any_call(notification.id)

    @patch("apps.notification.infra.task.send_to_pubsub.delay")
    def test_study_review_request_created(self, mock_delay: MagicMock) -> None:
        """스터디 그룹 후기 작성 요청 알림 테스트"""
        GroupMember.objects.create(study_group_id=self.study_group, user_id=self.applicant, is_leader=False)
        self.study_group.status = StudyGroup.StudyGroupStatusChoices.ENDED
        self.study_group.save()

        notification = Notification.objects.filter(type=Notification.NotificationType.STUDY_REVIEW_REQUEST)

        self.assertEqual(notification.count(), 3)

        notification1 = notification.get(user=self.existing_member)
        expected_content = f"오늘은 {self.study_group.name}의 종료일이에요! 스터디 후기를 기록해주세요!"
        self.assertEqual(notification1.content, expected_content)
        assert notification1.back_url_link is not None
        self.assertIn("", notification1.back_url_link)

        notification2 = notification.get(user=self.applicant)
        self.assertEqual(notification2.content, expected_content)
        self.assertEqual(mock_delay.call_count, 3)

    @patch("apps.notification.infra.task.send_to_pubsub.delay")
    def test_study_record_request_created(self, mock_delay: MagicMock) -> None:
        """스터디 기록 작성 알림 테스트"""
        StudyNote.objects.create(
            study_group_id=self.study_group.id,
            author=self.applicant,
            title="trouble shooting",
            content="mypy 파이썬 타입 힌트 오류 해결",
        )

        notification = Notification.objects.filter(type=Notification.NotificationType.STUDY_NOTE_CREATE)

        self.assertEqual(notification.count(), 2)
        notification_for_author = notification.get(user=self.author)
        expected_content = (
            f"{self.applicant.nickname}님이 {self.study_group.name}에 스터디 기록을 작성하셨습니다. 확인해보세요!"
        )

        self.assertEqual(notification_for_author.content, expected_content)
        self.assertEqual(mock_delay.call_count, 2)
        mock_delay.assert_called_with(notification_for_author.id)
