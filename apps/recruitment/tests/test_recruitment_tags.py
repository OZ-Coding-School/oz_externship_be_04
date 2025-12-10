import uuid
from datetime import datetime, timedelta
from typing import List, TypedDict

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.recruitment.models import Recruitment, Tag
from apps.study_groups.models import StudyGroup
from apps.users.models import User

UserModel = get_user_model()


class RecruitmentData(TypedDict):
    study_group: int
    title: str
    content: str
    estimated_fee: int
    expected_headcount: int
    close_at: datetime
    tags: List[int]
    files: List[dict[str, str]]
    image_urls: List[str]


class TestRecruitmentTags(APITestCase):

    def setUp(self) -> None:
        # 테스트 유저 생성
        self.user = User.objects.create(
            email="test@example.com",
            name="test",
            nickname="test1",
            phone_number="01012345678",
            gender="F",
            birthday="2000-01-01",
            profile_img_url="http://example.com",
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)

        # 태그 생성
        self.tag1 = Tag.objects.create(name="Python")
        self.tag2 = Tag.objects.create(name="Django")
        self.tag3 = Tag.objects.create(name="Database")
        self.tag4 = Tag.objects.create(name="JavaScript")
        self.tag5 = Tag.objects.create(name="AWS")
        self.tag6 = Tag.objects.create(name="FastAPI")

        # 스터디 그룹
        self.study_group = StudyGroup.objects.create(
            name="Python 스터디",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=(timezone.now() + timedelta(days=14)),
            status="ONGOING",
        )

        # 공고 생성용 데이터
        self.valid_data: RecruitmentData = {
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

        # Recruitment 생성
        self.recruitment = Recruitment.objects.create(
            study_group=self.study_group,
            title=self.valid_data["title"],
            content=self.valid_data["content"],
            estimated_fee=self.valid_data["estimated_fee"],
            expected_headcount=self.valid_data["expected_headcount"],
            close_at=self.valid_data["close_at"],
            author=self.user,
        )

        self.url = reverse("recruitment-tag", args=[self.recruitment.uuid])

    def test_get_recruitment_tags_empty(self) -> None:
        """공고에 태그가 없으면 빈 리스트 반환"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["tags"], [])

    def test_update_recruitment_tags_success(self) -> None:
        """공고 태그 정상 업데이트"""
        tag_ids = [self.tag1.id, self.tag2.id, self.tag3.id]
        response = self.client.put(self.url, {"tags": tag_ids}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["tags"]), 3)

    def test_update_recruitment_tags_exceed_limit(self) -> None:
        """태그 5개 초과 시 400 에러"""
        tag_ids = [self.tag1.id, self.tag2.id, self.tag3.id, self.tag4.id, self.tag5.id, self.tag6.id]
        response = self.client.put(self.url, {"tags": tag_ids}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        if "tags" in response.data:
            self.assertIn("태그는 5개이상 등록 할수 없습니다.", str(response.data["tags"][0]))
        else:
            self.assertIn("태그는 5개이상 등록 할수 없습니다.", str(response.data.get("error_detail")))

    def test_update_recruitment_tags_duplicate_ids(self) -> None:
        """태그 중복 선택 시 400 에러"""
        tag_ids = [self.tag1.id, self.tag1.id, self.tag2.id]
        response = self.client.put(self.url, {"tags": tag_ids}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        if "tags" in response.data:
            self.assertIn("중복될 수 없습니다", str(response.data["tags"][0]))
        else:
            self.assertIn("중복될 수 없습니다", str(response.data.get("error_detail")))

    def test_update_recruitment_tags_invalid_id(self) -> None:
        """존재하지 않는 태그 ID 포함 시 400 에러"""
        tag_ids = [999]  # 존재하지 않는 태그
        response = self.client.put(self.url, {"tags": tag_ids}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("존재하지 않는 태그 ID가 포함되어 있습니다.", response.data["error_detail"])

    def test_get_recruitment_tags_not_found(self) -> None:
        """존재하지 않는 공고 조회 시 404 반환"""
        invalid_id = uuid.uuid4()  # 존재하지 않는 공고 ID
        url = reverse("recruitment-tag", args=[invalid_id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("해당 공고를 찾을 수 없습니다.", response.data["error_detail"])

    def test_update_recruitment_tags_not_found(self) -> None:
        """존재하지 않는 공고에 태그 수정 시 404 반환"""
        invalid_id = uuid.uuid4()
        url = reverse("recruitment-tag", args=[invalid_id])

        response = self.client.put(url, {"tags": [self.tag1.id]}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("해당 공고를 찾을 수 없습니다.", response.data["error_detail"])
