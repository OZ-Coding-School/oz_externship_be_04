from unittest import TestCase
from unittest.mock import Mock

from apps.application.serializers.application_serializers import (
    ApplicantRecruitmentMinimalSerializer,
    ApplicantSummarySerializer,
    ApplicationCreateSerializer,
    RecruitmentSummarySerializer,
)


class TestApplicationSerializersUnit(TestCase):

    def test_applicant_recruitment_minimal_serializer(self) -> None:
        mock_recruitment = Mock(uuid="abc-123", title="테스트 공고")

        serializer = ApplicantRecruitmentMinimalSerializer(mock_recruitment)
        data = serializer.data

        self.assertEqual(data["uuid"], "abc-123")
        self.assertEqual(data["title"], "테스트 공고")

    def test_applicant_summary_serializer(self) -> None:
        mock_image = Mock()
        mock_image.url = "/media/users/profiles/backgr.PNG"
        mock_user = Mock(id=1, nickname="홍길동", gender="M", profile_img_url=mock_image)

        serializer = ApplicantSummarySerializer(mock_user)
        data = serializer.data

        self.assertEqual(data["id"], 1)
        self.assertEqual(data["nickname"], "홍길동")
        self.assertEqual(data["gender"], "M")
        self.assertEqual(data["profile_img_url"], "/media/users/profiles/backgr.PNG")

    def test_recruitment_summary_serializer(self) -> None:
        """Recruitment Summary 테스트"""
        from datetime import datetime, timezone
        from types import SimpleNamespace

        mock_recruitment = Mock(
            uuid="rec-123",
            title="테스트 모집",
            expected_headcount=10,
            close_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            lectures=[],
            tags=[],
        )

        mock_recruitment.study_group = SimpleNamespace(end_at=datetime(2025, 2, 1, 0, 0, 0, tzinfo=timezone.utc))

        serializer = RecruitmentSummarySerializer(mock_recruitment)
        data = serializer.data

        self.assertEqual(data["uuid"], "rec-123")
        self.assertEqual(data["title"], "테스트 모집")
        self.assertEqual(data["expected_headcount"], 10)
        self.assertEqual(data["thumbnail_img_url"], "/default/recruitment/rec-123/thumbnail.png")

    def test_application_create_serializer_success(self) -> None:
        payload = {
            "self_introduction": "Hi",
            "motivation": "Good",
            "objective": "Goal",
            "available_time": "Evening",
            "has_study_experience": True,
            "study_experience": "프로젝트 경험",
        }

        serializer = ApplicationCreateSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_application_create_serializer_fail(self) -> None:
        payload = {
            "self_introduction": "Hi",
            "motivation": "Good",
            "objective": "Goal",
            "available_time": "Evening",
            "has_study_experience": True,
            "study_experience": "",
        }

        serializer = ApplicationCreateSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("study_experience", serializer.errors)
