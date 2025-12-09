from datetime import date, timedelta
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apps.recruitment.models import Recruitment, RecruitmentBookmarks
from apps.recruitment.views.recruitment_bookmarks import (
    RecruitmentBookmarkDeleteView,
    RecruitmentBookmarkListCreateView,
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
        )

    @staticmethod
    def create_bookmark(user: User, recruitment: Recruitment) -> RecruitmentBookmarks:
        """테스트 북마크 생성"""
        return RecruitmentBookmarks.objects.create(user_id=user, recruitment_id=recruitment)


class BaseBookmarkTestCase(TestCase):
    """공통 테스트 베이스 클래스"""

    def setUp(self) -> None:
        """공통 setUp"""
        self.factory = APIRequestFactory()
        self.data_factory = TestDataFactory()

        self.user = self.data_factory.create_user()
        self.other_user = self.data_factory.create_user(email="other@test.com", nickname="다른사람")
        self.study_group = self.data_factory.create_study_group()

    def create_authenticated_request(
        self, method: str, user: User | None = None, data: dict[str, Any] | None = None
    ) -> Request:
        """인증된 Request 객체 생성"""
        user = user or self.user

        if method == "GET":
            request = self.factory.get("/")
        elif method == "POST":
            request = self.factory.post("/", data=data, format="json")
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

    def create_bookmark(self, user: User | None = None, recruitment: Recruitment | None = None) -> RecruitmentBookmarks:
        """테스트용 북마크 생성 헬퍼"""
        user = user or self.user
        recruitment = recruitment or self.create_recruitment()
        return self.data_factory.create_bookmark(user, recruitment)


class RecruitmentBookmarkListCreateViewTest(BaseBookmarkTestCase):
    """북마크 목록 조회 및 추가 테스트 (Unit Test)"""

    def setUp(self) -> None:
        super().setUp()
        self.view = RecruitmentBookmarkListCreateView()
        self.recruitment = self.create_recruitment(title="북마크할 공고")

    def test_create_bookmark_success(self) -> None:
        """북마크 추가 성공"""
        data = {"recruitment_uuid": str(self.recruitment.uuid)}
        request = self.create_authenticated_request("POST", user=self.user, data=data)

        response = self.view.post(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "북마크가 추가되었습니다.")
        self.assertTrue(
            RecruitmentBookmarks.objects.filter(user_id_id=self.user.id, recruitment_id_id=self.recruitment.id).exists()
        )

    def test_create_bookmark_unauthenticated(self) -> None:
        """비인증 사용자 북마크 추가 실패"""
        data = {"recruitment_uuid": str(self.recruitment.uuid)}
        request = self.factory.post("/", data=data, format="json")
        request.user = MagicMock()
        request.user.is_authenticated = False
        request = Request(request)

        # IsAuthenticated 권한 체크
        with self.assertRaises(Exception):
            self.view.check_permissions(request)

    def test_create_bookmark_duplicate(self) -> None:
        """중복 북마크 추가 실패"""
        self.data_factory.create_bookmark(self.user, self.recruitment)

        data = {"recruitment_uuid": str(self.recruitment.uuid)}
        request = self.create_authenticated_request("POST", user=self.user, data=data)

        response = self.view.post(request)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("이미 북마크한 공고입니다", response.data["error_detail"])

    def test_create_bookmark_recruitment_not_found(self) -> None:
        """존재하지 않는 공고 북마크 실패"""
        fake_uuid = uuid4()
        data = {"recruitment_uuid": str(fake_uuid)}
        request = self.create_authenticated_request("POST", user=self.user, data=data)

        response = self.view.post(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_bookmarks_success(self) -> None:
        """북마크 목록 조회 성공"""
        # 15개 북마크 생성
        for i in range(15):
            recruitment = self.create_recruitment(title=f"내 북마크 공고 {i+1}")
            self.data_factory.create_bookmark(self.user, recruitment)

        request = self.create_authenticated_request("GET", user=self.user)
        response = self.view.get(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)  # 페이지 크기 10

    def test_list_bookmarks_unauthenticated(self) -> None:
        """비인증 사용자 목록 조회 실패"""
        request = self.factory.get("/")
        request.user = MagicMock()
        request.user.is_authenticated = False
        request = Request(request)

        # IsAuthenticated 권한 체크
        with self.assertRaises(Exception):
            self.view.check_permissions(request)

    def test_list_bookmarks_only_own_bookmarks(self) -> None:
        """자신의 북마크만 조회됨"""
        # 내 북마크 15개
        for i in range(15):
            recruitment = self.create_recruitment(title=f"내 북마크 공고 {i+1}")
            self.data_factory.create_bookmark(self.user, recruitment)

        # 다른 사람 북마크 5개
        for i in range(5):
            recruitment = self.create_recruitment(author=self.other_user, title=f"다른 사람 공고 {i+1}")
            self.data_factory.create_bookmark(self.other_user, recruitment)

        request = self.factory.get("/", {"page_size": "20"})
        request.user = self.user
        request = Request(request)

        response = self.view.get(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 15)  # 자신의 15개만

    def test_list_bookmarks_search(self) -> None:
        """검색 기능 테스트"""
        recruitment = self.create_recruitment(title="Django 백엔드 스터디")
        self.data_factory.create_bookmark(self.user, recruitment)

        # 다른 북마크도 추가
        for i in range(5):
            other_recruitment = self.create_recruitment(title=f"React 공고 {i+1}")
            self.data_factory.create_bookmark(self.user, other_recruitment)

        request = self.factory.get("/", {"search": "Django"})
        request.user = self.user
        request = Request(request)

        response = self.view.get(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_list_bookmarks_cursor_pagination(self) -> None:
        """커서 페이지네이션 테스트"""
        for i in range(15):
            recruitment = self.create_recruitment(title=f"북마크 공고 {i+1}")
            self.data_factory.create_bookmark(self.user, recruitment)

        request = self.factory.get("/", {"page_size": "10"})
        request.user = self.user
        request = Request(request)

        response = self.view.get(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("next", response.data)
        self.assertIsNotNone(response.data["next"])


class RecruitmentBookmarkDeleteViewTest(BaseBookmarkTestCase):
    """북마크 삭제 테스트 (Unit Test)"""

    def setUp(self) -> None:
        super().setUp()
        self.view = RecruitmentBookmarkDeleteView()
        self.recruitment = self.create_recruitment(title="북마크된 공고")
        self.bookmark = self.data_factory.create_bookmark(self.user, self.recruitment)

    def test_delete_bookmark_success(self) -> None:
        """북마크 삭제 성공"""
        request = self.create_authenticated_request("DELETE", user=self.user)
        response = self.view.delete(request, bookmark_id=self.bookmark.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "북마크가 취소되었습니다.")
        self.assertFalse(RecruitmentBookmarks.objects.filter(id=self.bookmark.id).exists())

    def test_delete_bookmark_unauthenticated(self) -> None:
        """비인증 사용자 삭제 실패"""
        request = self.factory.delete("/")
        request.user = MagicMock()
        request.user.is_authenticated = False
        request = Request(request)

        # IsAuthenticated 권한 체크
        with self.assertRaises(Exception):
            self.view.check_permissions(request)

    def test_delete_bookmark_unauthorized(self) -> None:
        """다른 사용자의 북마크 삭제 실패"""
        request = self.create_authenticated_request("DELETE", user=self.other_user)
        response = self.view.delete(request, bookmark_id=self.bookmark.id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("권한이 없습니다", response.data["error_detail"])

    def test_delete_bookmark_not_found(self) -> None:
        """존재하지 않는 북마크 삭제 실패"""
        request = self.create_authenticated_request("DELETE", user=self.user)
        response = self.view.delete(request, bookmark_id=999999)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("북마크 내역을 찾을 수 없습니다", response.data["error_detail"])


class BookmarkIntegrationTest(BaseBookmarkTestCase):
    """북마크 통합 시나리오 테스트 (Unit Test)"""

    def setUp(self) -> None:
        super().setUp()
        self.list_create_view = RecruitmentBookmarkListCreateView()
        self.delete_view = RecruitmentBookmarkDeleteView()

    def test_bookmark_full_cycle(self) -> None:
        """북마크 생성 -> 조회 -> 삭제 전체 플로우"""
        recruitment = self.create_recruitment(title="통합 테스트 공고")

        # 1. 북마크 추가
        data = {"recruitment_uuid": str(recruitment.uuid)}
        request = self.create_authenticated_request("POST", user=self.user, data=data)
        response = self.list_create_view.post(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2. 북마크 목록 조회
        request = self.create_authenticated_request("GET", user=self.user)
        response = self.list_create_view.get(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

        # 3. 북마크 삭제
        bookmark = RecruitmentBookmarks.objects.get(user_id_id=self.user.id, recruitment_id_id=recruitment.id)
        request = self.create_authenticated_request("DELETE", user=self.user)
        response = self.delete_view.delete(request, bookmark_id=bookmark.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(RecruitmentBookmarks.objects.filter(id=bookmark.id).exists())

    def test_multiple_users_bookmarking_same_recruitment(self) -> None:
        """여러 사용자가 같은 공고를 북마크"""
        recruitment = self.create_recruitment(title="인기 공고")

        # User1 북마크 추가
        data = {"recruitment_uuid": str(recruitment.uuid)}
        request = self.create_authenticated_request("POST", user=self.user, data=data)
        response = self.list_create_view.post(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # User2 북마크 추가
        request = self.create_authenticated_request("POST", user=self.other_user, data=data)
        response = self.list_create_view.post(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        bookmark_count = RecruitmentBookmarks.objects.filter(recruitment_id_id=recruitment.id).count()
        self.assertEqual(bookmark_count, 2)
