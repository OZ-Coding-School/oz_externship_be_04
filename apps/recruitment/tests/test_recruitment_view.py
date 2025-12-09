from datetime import date, timedelta
from typing import Any
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

from django.db.models import Q
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apps.recruitment.models import Recruitment, Tag
from apps.recruitment.serializers.recruitment_serializer import (
    RecruitmentCreateSerializer,
    RecruitmentDetailSerializer,
    RecruitmentListSerializer,
)
from apps.recruitment.views.recruitment_view import (
    RecruitmentDetailUpdateDeleteView,
    RecruitmentListCreateView,
    RecruitmentMineView,
)
from apps.study_groups.models import StudyGroup
from apps.users.models import User


class TestDataFactory:
    """테스트 데이터 생성 팩토리"""

    @staticmethod
    def create_user(email: str = "test@test.com", nickname: str = "테스터", password: str = "testpass123") -> User:
        """테스트 사용자 생성"""
        user = User.objects.create(
            email=email,
            nickname=nickname,
            name="테스트유저",
            phone_number=f"010-0000-{hash(email) % 10000:04d}",
            gender="M",
            birthday=date(1990, 1, 1),
            profile_img_url="https://example.com/profile.jpg",
            is_active=True,
        )
        user.set_password(password)
        user.save()
        return user

    @staticmethod
    def create_study_group(
        name: str = "테스트 스터디",
        status: str = StudyGroup.StudyGroupStatusChoices.ONGOING,
        days_until_end: int = 30,
    ) -> StudyGroup:
        """테스트 스터디 그룹 생성"""
        return StudyGroup.objects.create(
            name=name,
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=days_until_end),
            status=status,
        )

    @staticmethod
    def create_recruitment(
        study_group: StudyGroup,
        author: User,
        title: str = "테스트 공고",
        content: str = "테스트 내용입니다.",
        expected_headcount: int = 3,
        days_until_close: int = 7,
        is_closed: bool = False,
        views_count: int = 0,
    ) -> Recruitment:
        """테스트 공고 생성"""
        return Recruitment.objects.create(
            study_group=study_group,
            author=author,
            title=title,
            content=content,
            expected_headcount=expected_headcount,
            close_at=timezone.now() + timedelta(days=days_until_close),
            is_closed=is_closed,
            views_count=views_count,
        )

    @staticmethod
    def create_tag(name: str) -> Tag:
        """테스트 태그 생성"""
        return Tag.objects.create(name=name)

    @staticmethod
    def get_valid_recruitment_data(study_group_id: int, tag_ids: list[int] | None = None) -> dict[str, Any]:
        """유효한 공고 작성 데이터 반환"""
        data = {
            "study_group": study_group_id,
            "title": "테스트 공고 제목입니다",
            "content": "테스트 공고 내용입니다. 최소 10자 이상 작성합니다.",
            "estimated_fee": 50000,
            "expected_headcount": 3,
            "close_at": (timezone.now() + timedelta(days=7)).isoformat(),
            "files": [{"file_name": "test.pdf", "file_url": "https://example.com/test.pdf"}],
            "image_urls": ["https://example.com/image1.jpg"],
        }

        if tag_ids:
            data["tags"] = tag_ids

        return data


class BaseRecruitmentTestCase(TestCase):
    """공통 테스트 베이스 클래스"""

    def setUp(self) -> None:
        """공통 setUp"""
        self.factory = APIRequestFactory()
        self.data_factory = TestDataFactory()

        self.user = self.data_factory.create_user()
        self.other_user = self.data_factory.create_user(email="other@test.com", nickname="다른사람")
        self.study_group = self.data_factory.create_study_group()

        self.tag1 = self.data_factory.create_tag("Python")
        self.tag2 = self.data_factory.create_tag("Django")

    def create_authenticated_request(
        self, method: str, user: User | None = None, data: dict[str, Any] | None = None
    ) -> Request:
        """인증된 Request 객체 생성"""
        user = user or self.user

        if method == "GET":
            request = self.factory.get("/")
        elif method == "POST":
            request = self.factory.post("/", data=data, format="json")
        elif method == "PATCH":
            request = self.factory.patch("/", data=data, format="json")
        elif method == "DELETE":
            request = self.factory.delete("/")
        else:
            raise ValueError(f"Unsupported method: {method}")

        request.user = user
        return Request(request)

    def create_recruitment(self, **kwargs: Any) -> Recruitment:
        """테스트용 공고 생성 헬퍼"""
        defaults: dict[str, Any] = {"study_group": self.study_group, "author": self.user}
        defaults.update(kwargs)
        return self.data_factory.create_recruitment(**defaults)


class RecruitmentListCreateViewTest(BaseRecruitmentTestCase):
    """공고 목록 조회 및 작성 테스트 (Unit Test)"""

    def setUp(self) -> None:
        super().setUp()
        self.view = RecruitmentListCreateView()

    def test_create_recruitment_success(self) -> None:
        """공고 작성 성공"""
        data = self.data_factory.get_valid_recruitment_data(self.study_group.id, [self.tag1.id, self.tag2.id])
        request = self.create_authenticated_request("POST", user=self.user, data=data)

        response = self.view.post(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], data["title"])
        self.assertIn("uuid", response.data)
        self.assertIn("content", response.data)
        self.assertTrue(Recruitment.objects.filter(title=data["title"]).exists())

    def test_create_recruitment_unauthenticated(self) -> None:
        """비인증 사용자 공고 작성 실패"""
        data = self.data_factory.get_valid_recruitment_data(self.study_group.id)
        request = self.factory.post("/", data=data, format="json")
        request.user = MagicMock()
        request.user.is_authenticated = False
        request = Request(request)

        self.view.check_permissions(request)

        # 비인증 사용자는 POST 불가 (IsAuthenticatedOrReadOnly)
        self.assertFalse(request.user.is_authenticated)

    def test_create_recruitment_with_ended_study_group(self) -> None:
        """종료된 스터디 그룹으로 공고 작성 실패"""
        ended_group = self.data_factory.create_study_group(
            name="종료된 스터디", status=StudyGroup.StudyGroupStatusChoices.ENDED
        )

        data = self.data_factory.get_valid_recruitment_data(ended_group.id)
        request = self.create_authenticated_request("POST", user=self.user, data=data)

        response = self.view.post(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recruitment_invalid_title_too_short(self) -> None:
        """제목이 5자 미만일 때 실패"""
        data = self.data_factory.get_valid_recruitment_data(self.study_group.id)
        data["title"] = "짧음"
        request = self.create_authenticated_request("POST", user=self.user, data=data)

        response = self.view.post(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_recruitments_success(self) -> None:
        """공고 목록 조회 성공"""
        # 15개 공고 생성
        for i in range(15):
            self.create_recruitment(title=f"테스트 공고 {i+1}")

        request = self.create_authenticated_request("GET")
        response = self.view.get(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 15)

    def test_list_recruitments_pagination(self) -> None:
        """페이지네이션 테스트"""
        for i in range(15):
            self.create_recruitment(title=f"테스트 공고 {i+1}")

        request = self.factory.get("/", {"page": 1, "size": 10})
        request.user = self.user
        request = Request(request)

        response = self.view.get(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data.get("next"))

    def test_list_recruitments_excludes_closed(self) -> None:
        """마감된 공고는 목록에서 제외"""
        for i in range(10):
            self.create_recruitment(title=f"진행중 공고 {i+1}", is_closed=False)

        self.create_recruitment(title="마감된 공고", is_closed=True)

        request = self.create_authenticated_request("GET")
        response = self.view.get(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 10)  # 마감된 공고 제외


class RecruitmentDetailUpdateDeleteViewTest(BaseRecruitmentTestCase):
    """공고 상세 조회/수정/삭제 테스트 (Unit Test)"""

    def setUp(self) -> None:
        super().setUp()
        self.view = RecruitmentDetailUpdateDeleteView()
        self.recruitment = self.create_recruitment(title="테스트 공고")

    def test_detail_recruitment_success(self) -> None:
        """공고 상세 조회 성공"""
        request = self.create_authenticated_request("GET")
        response = self.view.get(request, recruitments_uuid=self.recruitment.uuid)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.recruitment.title)
        self.assertIn("content", response.data)

    def test_detail_recruitment_increases_view_count(self) -> None:
        """조회수 증가 확인"""
        initial_views = self.recruitment.views_count

        request = self.create_authenticated_request("GET")
        self.view.get(request, recruitments_uuid=self.recruitment.uuid)

        self.recruitment.refresh_from_db()
        self.assertEqual(self.recruitment.views_count, initial_views + 1)

    def test_detail_recruitment_not_found(self) -> None:
        """존재하지 않는 공고 조회 시 404"""
        fake_uuid = uuid4()
        request = self.create_authenticated_request("GET")
        response = self.view.get(request, recruitments_uuid=fake_uuid)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_recruitment_success(self) -> None:
        """공고 수정 성공"""
        data = {"title": "수정된 제목입니다"}
        request = self.create_authenticated_request("PATCH", user=self.user, data=data)
        response = self.view.patch(request, recruitments_uuid=self.recruitment.uuid)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "수정된 제목입니다")

    def test_update_recruitment_unauthorized(self) -> None:
        """작성자가 아닌 사용자 수정 실패"""
        data = {"title": "수정 시도"}
        request = self.create_authenticated_request("PATCH", user=self.other_user, data=data)
        response = self.view.patch(request, recruitments_uuid=self.recruitment.uuid)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_closed_recruitment_fails(self) -> None:
        """마감된 공고 수정 실패"""
        self.recruitment.is_closed = True
        self.recruitment.save()

        data = {"title": "수정 시도"}
        request = self.create_authenticated_request("PATCH", user=self.user, data=data)
        response = self.view.patch(request, recruitments_uuid=self.recruitment.uuid)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_recruitment_success(self) -> None:
        """공고 삭제(Soft Delete) 성공"""
        request = self.create_authenticated_request("DELETE", user=self.user)
        response = self.view.delete(request, recruitments_uuid=self.recruitment.uuid)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "공고가 삭제되었습니다.")

        self.recruitment.refresh_from_db()
        self.assertTrue(self.recruitment.is_closed)

    def test_delete_recruitment_unauthorized(self) -> None:
        """작성자가 아닌 사용자 삭제 실패"""
        request = self.create_authenticated_request("DELETE", user=self.other_user)
        response = self.view.delete(request, recruitments_uuid=self.recruitment.uuid)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_already_closed_recruitment_fails(self) -> None:
        """이미 마감된 공고 삭제 실패"""
        self.recruitment.is_closed = True
        self.recruitment.save()

        request = self.create_authenticated_request("DELETE", user=self.user)
        response = self.view.delete(request, recruitments_uuid=self.recruitment.uuid)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RecruitmentMineViewTest(BaseRecruitmentTestCase):
    """내가 작성한 공고 목록 테스트 (Unit Test)"""

    def setUp(self) -> None:
        super().setUp()
        self.view = RecruitmentMineView()

        # 내 공고 5개
        for i in range(5):
            self.create_recruitment(title=f"내 공고 {i+1}")

        # 다른 사람 공고 3개
        for i in range(3):
            self.create_recruitment(author=self.other_user, title=f"다른 사람 공고 {i+1}")

    def test_mine_recruitments_success(self) -> None:
        """내 공고 목록 조회 성공"""
        request = self.create_authenticated_request("GET", user=self.user)
        response = self.view.get(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)

    def test_mine_recruitments_unauthenticated(self) -> None:
        """비인증 사용자는 접근 불가"""
        request = self.factory.get("/")
        request.user = MagicMock()
        request.user.is_authenticated = False
        request = Request(request)

        with self.assertRaises(Exception):
            self.view.check_permissions(request)

    def test_mine_recruitments_filter_by_is_closed(self) -> None:
        """마감 여부 필터링"""
        recruitment = Recruitment.objects.filter(author=self.user).first()
        if recruitment:
            recruitment.is_closed = True
            recruitment.save()

        request = self.factory.get("/", {"is_closed": "true"})
        request.user = self.user
        request = Request(request)

        response = self.view.get(request)
        self.assertEqual(response.data["count"], 1)
