from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.recruitment.models import Recruitment, Tag
from apps.recruitment.serializers import (
    RecruitmentCreateSerializer,
    RecruitmentDetailSerializer,
    RecruitmentListSerializer,
    RecruitmentUpdateSerializer,
)
from apps.study_groups.models import StudyGroup
from apps.users.models import User


class RecruitmentSerializerTestCase(TestCase):
    def setUp(self) -> None:
        # 유저, 스터디 그룹, 태그 생성
        self.user = User.objects.create(
            email="test@test.com",
            password="password",
            name="홍길동",
            nickname="hong",
            phone_number="01012345678",
            gender="M",
            birthday="2000-01-01",
            is_active=True,
        )
        self.study_group = StudyGroup.objects.create(
            name="Python 스터디",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=(timezone.now() + timedelta(days=14)),
            status="ONGOING",
        )
        self.tag1 = Tag.objects.create(name="Python")
        self.tag2 = Tag.objects.create(name="Django")

        # 공고 생성용 데이터
        self.valid_data = {
            "study_group": self.study_group.id,
            "title": "테스트 공고 제목",
            "content": "테스트 공고 내용입니다.",
            "estimated_fee": 10000,
            "expected_headcount": 5,
            "close_at": timezone.now() + timedelta(days=14),
            "tags": [self.tag1.id, self.tag2.id],
            "files": [{"file_name": "file1.pdf", "file_url": "http://file1.com"}],
            "image_urls": ["http://img1.com", "http://img2.com"],
        }

    def test_create_serializer_validation(self) -> None:
        """RecruitmentCreateSerializer 유효성 검증"""
        serializer = RecruitmentCreateSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_serializer_title_validation_fail(self) -> None:
        """제목 길이 검증 실패"""
        invalid_data = self.valid_data.copy()
        invalid_data["title"] = "제목"
        serializer = RecruitmentCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)

    def test_create_serializer_title_validation_success(self) -> None:
        """제목 길이 검증 성공"""
        valid_data = self.valid_data.copy()
        valid_data["title"] = "제목 길이 검증 하기"
        serializer = RecruitmentCreateSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_serializer_content_validation_fail(self) -> None:
        """내용 길이 검증 실패"""
        invalid_data = self.valid_data.copy()
        invalid_data["content"] = "내용"
        serializer = RecruitmentCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("content", serializer.errors)

    def test_create_serializer_content_validation_success(self) -> None:
        """내용 길이 검증 성공"""
        valid_data = self.valid_data.copy()
        valid_data["content"] = "recruitment_serializer 테스트용 내용입니다."
        serializer = RecruitmentCreateSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_serializer_tags_validation_fail(self) -> None:
        """태그 중복 검증 실패"""
        invalid_data = self.valid_data.copy()
        invalid_data["tags"] = [self.tag1.id, self.tag1.id]  # 중복 태그
        serializer = RecruitmentCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("tags", serializer.errors)

    def test_create_serializer_tags_validation_success(self) -> None:
        """태그 중복 검증 성공"""
        valid_data = self.valid_data.copy()
        valid_data["tags"] = [self.tag1.id, self.tag2.id]
        serializer = RecruitmentCreateSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_list_serializer_output(self) -> None:
        """RecruitmentListSerializer 테스트"""
        recruitment = Recruitment.objects.create(
            study_group=self.study_group,
            author=self.user,
            title="테스트 공고",
            content="상세 내용",
            estimated_fee=5000,
            expected_headcount=3,
            close_at=timezone.now() + timedelta(days=14),
        )
        serializer = RecruitmentListSerializer(recruitment)
        data = serializer.data
        self.assertIn("uuid", data)
        self.assertIn("lectures", data)
        self.assertIn("tags", data)

    def test_detail_serializer_output(self) -> None:
        """RecruitmentDetailSerializer 테스트"""
        recruitment = Recruitment.objects.create(
            study_group=self.study_group,
            author=self.user,
            title="테스트 공고",
            content="상세 내용",
            estimated_fee=5000,
            expected_headcount=3,
            close_at=timezone.now() + timedelta(days=14),
        )
        serializer = RecruitmentDetailSerializer(recruitment)
        data = serializer.data
        self.assertIn("uuid", data)
        self.assertIn("lectures", data)
        self.assertIn("tags", data)
        self.assertIn("files", data)
        self.assertIn("image_urls", data)

    def test_update_serializer_validation(self) -> None:
        """RecruitmentUpdateSerializer 유효성 검증"""
        serializer = RecruitmentUpdateSerializer(
            data={
                "title": "업데이트 제목",
                "content": "업데이트 내용 충분히 긴 내용",
                "expected_headcount": 4,
            },
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
