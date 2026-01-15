from unittest import TestCase
from unittest.mock import Mock

from apps.application.serializers.admin_application_serializers import (
    AdminApplicantDetailSerializer,
    AdminApplicantSummarySerializer,
    AdminApplicationDetailSerializer,
    AdminApplicationListSerializer,
    AdminRecruitmentDetailSerializer,
    AdminRecruitmentSummarySerializer,
)


class TestAdminApplicationSerializers(TestCase):

    def test_admin_applicant_summary_serializer(self) -> None:
        """지원자 요약 직렬화 테스트"""
        mock_user = Mock(id=1, nickname="홍길동", email="hong@test.com")

        serializer = AdminApplicantSummarySerializer(mock_user)
        data = serializer.data

        self.assertEqual(data["id"], 1)
        self.assertEqual(data["nickname"], "홍길동")
        self.assertEqual(data["email"], "hong@test.com")

    def test_admin_applicant_detail_serializer(self) -> None:
        """지원자 상세 직렬화 테스트"""
        mock_user = Mock(
            id=1,
            nickname="홍길동",
            email="hong@test.com",
            gender="M",
            profile_img_url="/img.png",
        )

        serializer = AdminApplicantDetailSerializer(mock_user)
        data = serializer.data

        self.assertEqual(data["id"], 1)
        self.assertEqual(data["nickname"], "홍길동")
        self.assertEqual(data["email"], "hong@test.com")
        self.assertEqual(data["gender"], "M")
        self.assertEqual(data["profile_img_url"], "/img.png")

    def test_admin_recruitment_summary_serializer(self) -> None:
        """공고 요약 직렬화 테스트"""
        mock_rec = Mock(id=100, uuid="rec-123", title="백엔드 모집")

        serializer = AdminRecruitmentSummarySerializer(mock_rec)
        data = serializer.data

        self.assertEqual(data["id"], 100)
        self.assertEqual(data["uuid"], "rec-123")
        self.assertEqual(data["title"], "백엔드 모집")

    def test_admin_recruitment_detail_serializer(self) -> None:
        """강의 & 태그 직렬화 테스트"""

        from types import SimpleNamespace

        # Lecture mock
        lecture1 = SimpleNamespace(id=1, title="파이썬", instructor="Alice")
        lecture2 = SimpleNamespace(id=2, title="장고", instructor="Bob")

        select_related_mock = Mock()
        select_related_mock.all.return_value = [
            SimpleNamespace(lecture=lecture1),
            SimpleNamespace(lecture=lecture2),
        ]

        study_group_mock = Mock()
        study_group_mock.studylecture_study_groups.select_related.return_value = select_related_mock

        tag1 = SimpleNamespace(id=1, name="Python")
        tag2 = SimpleNamespace(id=2, name="Django")

        recruitment_tag1 = SimpleNamespace(tag=tag1)
        recruitment_tag2 = SimpleNamespace(tag=tag2)

        mock_rec = Mock(
            id=100,
            title="백엔드 모집",
            expected_headcount=10,
            close_at="2025-01-01",
            study_group=study_group_mock,
        )
        mock_rec.recruitment_tags.all.return_value = [recruitment_tag1, recruitment_tag2]

        serializer = AdminRecruitmentDetailSerializer(mock_rec)
        data = serializer.data

        self.assertEqual(data["tags"][1]["name"], "Django")

    def test_admin_application_list_serializer(self) -> None:
        """관리자 목록 직렬화 테스트"""

        mock_rec = Mock(id=10, uuid="rec-001", title="테스트 공고")
        mock_user = Mock(id=1, nickname="홍길동", email="hong@test.com")

        mock_app = Mock(
            id=1,
            uuid="app-123",
            status="SUBMITTED",
            created_at="2025-01-01",
            updated_at="2025-01-02",
            recruitment=mock_rec,
            applicant=mock_user,
        )

        serializer = AdminApplicationListSerializer(mock_app)
        data = serializer.data

        self.assertEqual(data["id"], 1)
        self.assertEqual(data["recruitment"]["title"], "테스트 공고")
        self.assertEqual(data["applicant"]["nickname"], "홍길동")

    def test_admin_application_detail_serializer(self) -> None:
        """지원서 상세 직렬화 + DETAIL_FIELDS 테스트"""

        from types import SimpleNamespace

        # Lecture mock
        lecture1 = SimpleNamespace(id=1, title="A", instructor="X")
        lecture2 = SimpleNamespace(id=2, title="B", instructor="Y")

        select_related_mock = Mock()
        select_related_mock.all.return_value = [
            SimpleNamespace(lecture=lecture1),
            SimpleNamespace(lecture=lecture2),
        ]

        sg_mock = Mock()
        sg_mock.studylecture_study_groups.select_related.return_value = select_related_mock

        tag1 = SimpleNamespace(id=1, name="Python")
        tag2 = SimpleNamespace(id=2, name="Django")

        rt1 = SimpleNamespace(tag=tag1)
        rt2 = SimpleNamespace(tag=tag2)

        mock_recruitment = Mock(
            id=100,
            title="백엔드 모집",
            expected_headcount=10,
            close_at="2025-01-01",
            study_group=sg_mock,
        )
        mock_recruitment.recruitment_tags.all.return_value = [rt1, rt2]

        # applicant mock
        mock_applicant = Mock(
            id=1,
            nickname="홍길동",
            email="hong@example.com",
            gender="M",
            profile_img_url="/img.png",
        )

        # application mock
        mock_app = Mock(
            id=1,
            uuid="app-123",
            status="SUBMITTED",
            created_at="2025-01-01",
            updated_at="2025-01-02",
            recruitment=mock_recruitment,
            applicant=mock_applicant,
            self_introduction="Hi",
            motivation="Good",
            objective="Goal",
            available_time="Evening",
            has_study_experience=True,
            study_experience="경험 있음",
        )

        serializer = AdminApplicationDetailSerializer(mock_app)
        data = serializer.data

        self.assertEqual(data["recruitment"]["tags"][1]["name"], "Django")
