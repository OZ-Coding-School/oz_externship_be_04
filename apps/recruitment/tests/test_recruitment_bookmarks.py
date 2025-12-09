from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.recruitment.models import Recruitment, RecruitmentBookmarks
from apps.study_groups.models import StudyGroup
from apps.users.models import User


class TestDataFactory:
    """테스트 데이터 생성 팩토리"""

    @staticmethod
    def create_user(email: str = "test@test.com", nickname: str = "테스터", password: str = "testpass123") -> User:
        """테스트 사용자 생성"""
        return User.objects.create_user(email=email, password=password, nickname=nickname)

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
        self.client = APIClient()
        self.factory = TestDataFactory()

        self.user = self.factory.create_user()
        self.other_user = self.factory.create_user(email="other@test.com", nickname="다른사람")
        self.study_group = self.factory.create_study_group()

    def authenticate(self, user: User | None = None) -> None:
        """사용자 인증"""
        user = user or self.user
        self.client.force_authenticate(user=user)

    def create_recruitment(self, **kwargs) -> Recruitment:
        """테스트용 공고 생성 헬퍼"""
        defaults = {"study_group": self.study_group, "author": self.user}
        defaults.update(kwargs)
        return self.factory.create_recruitment(**defaults)

    def create_bookmark(self, user: User | None = None, recruitment: Recruitment | None = None) -> RecruitmentBookmarks:
        """테스트용 북마크 생성 헬퍼"""
        user = user or self.user
        recruitment = recruitment or self.create_recruitment()
        return self.factory.create_bookmark(user, recruitment)


class RecruitmentBookmarkCreateViewTest(BaseBookmarkTestCase):
    """북마크 추가 테스트"""

    def setUp(self) -> None:
        super().setUp()
        self.recruitment = self.create_recruitment(title="북마크할 공고")

    def test_create_bookmark_success(self) -> None:
        """북마크 추가 성공"""
        self.authenticate()
        data = {"recruitment_uuid": str(self.recruitment.uuid)}

        response = self.client.post("/api/recruitment-bookmarks/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "북마크가 추가되었습니다.")
        self.assertTrue(
            RecruitmentBookmarks.objects.filter(user_id=self.user, recruitment_id=self.recruitment).exists()
        )

    def test_create_bookmark_unauthenticated(self) -> None:
        """비인증 사용자 북마크 추가 실패"""
        data = {"recruitment_uuid": str(self.recruitment.uuid)}
        response = self.client.post("/api/recruitment-bookmarks/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_bookmark_duplicate(self) -> None:
        """중복 북마크 추가 실패"""
        self.factory.create_bookmark(self.user, self.recruitment)

        self.authenticate()
        data = {"recruitment_uuid": str(self.recruitment.uuid)}

        response = self.client.post("/api/recruitment-bookmarks/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("이미 북마크한 공고입니다", response.data["error_detail"])

    def test_create_bookmark_recruitment_not_found(self) -> None:
        """존재하지 않는 공고 북마크 실패"""
        self.authenticate()
        from uuid import uuid4

        fake_uuid = uuid4()
        data = {"recruitment_uuid": str(fake_uuid)}

        response = self.client.post("/api/recruitment-bookmarks/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RecruitmentBookmarkListViewTest(BaseBookmarkTestCase):
    """북마크 목록 조회 테스트"""

    def setUp(self) -> None:
        super().setUp()
        for i in range(15):
            recruitment = self.create_recruitment(title=f"내 북마크 공고 {i+1}")
            self.factory.create_bookmark(self.user, recruitment)
        for i in range(5):
            recruitment = self.create_recruitment(author=self.other_user, title=f"다른 사람 공고 {i+1}")
            self.factory.create_bookmark(self.other_user, recruitment)

    def test_list_bookmarks_success(self) -> None:
        """북마크 목록 조회 성공"""
        self.authenticate()

        response = self.client.get("/api/recruitment-bookmarks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)

    def test_list_bookmarks_unauthenticated(self) -> None:
        """비인증 사용자 목록 조회 실패"""
        response = self.client.get("/api/recruitment-bookmarks/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_bookmarks_only_own_bookmarks(self) -> None:
        """자신의 북마크만 조회됨"""
        self.authenticate()

        response = self.client.get("/api/recruitment-bookmarks/?page_size=20")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 15)  # 자신의 15개만

    def test_list_bookmarks_search(self) -> None:
        """검색 기능 테스트"""
        recruitment = self.create_recruitment(title="Django 백엔드 스터디")
        self.factory.create_bookmark(self.user, recruitment)

        self.authenticate()
        response = self.client.get("/api/recruitment-bookmarks/?search=Django")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_list_bookmarks_cursor_pagination(self) -> None:
        """커서 페이지네이션 테스트"""
        self.authenticate()

        response = self.client.get("/api/recruitment-bookmarks/?page_size=10")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("next", response.data)
        self.assertIsNotNone(response.data["next"])


class RecruitmentBookmarkDeleteViewTest(BaseBookmarkTestCase):
    """북마크 삭제 테스트"""

    def setUp(self) -> None:
        super().setUp()
        self.recruitment = self.create_recruitment(title="북마크된 공고")
        self.bookmark = self.factory.create_bookmark(self.user, self.recruitment)

    def test_delete_bookmark_success(self) -> None:
        """북마크 삭제 성공"""
        self.authenticate()

        response = self.client.delete(f"/api/recruitment-bookmarks/{self.bookmark.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "북마크가 취소되었습니다.")
        self.assertFalse(RecruitmentBookmarks.objects.filter(id=self.bookmark.id).exists())

    def test_delete_bookmark_unauthenticated(self) -> None:
        """비인증 사용자 삭제 실패"""
        response = self.client.delete(f"/api/recruitment-bookmarks/{self.bookmark.id}/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_bookmark_unauthorized(self) -> None:
        """다른 사용자의 북마크 삭제 실패"""
        self.authenticate(self.other_user)

        response = self.client.delete(f"/api/recruitment-bookmarks/{self.bookmark.id}/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("권한이 없습니다", response.data["error_detail"])

    def test_delete_bookmark_not_found(self) -> None:
        """존재하지 않는 북마크 삭제 실패"""
        self.authenticate()

        response = self.client.delete("/api/recruitment-bookmarks/999999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("북마크 내역을 찾을 수 없습니다", response.data["error_detail"])


class BookmarkIntegrationTest(BaseBookmarkTestCase):
    """북마크 통합 시나리오 테스트"""

    def test_bookmark_full_cycle(self) -> None:
        """북마크 생성 -> 조회 -> 삭제 전체 플로우"""
        self.authenticate()

        recruitment = self.create_recruitment(title="통합 테스트 공고")

        data = {"recruitment_uuid": str(recruitment.uuid)}
        response = self.client.post("/api/recruitment-bookmarks/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get("/api/recruitment-bookmarks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

        bookmark = RecruitmentBookmarks.objects.get(user_id=self.user, recruitment_id=recruitment)
        response = self.client.delete(f"/api/recruitment-bookmarks/{bookmark.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(RecruitmentBookmarks.objects.filter(id=bookmark.id).exists())

    def test_multiple_users_bookmarking_same_recruitment(self) -> None:
        """여러 사용자가 같은 공고를 북마크"""
        recruitment = self.create_recruitment(title="인기 공고")

        self.authenticate(self.user)
        data = {"recruitment_uuid": str(recruitment.uuid)}
        response = self.client.post("/api/recruitment-bookmarks/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.authenticate(self.other_user)
        response = self.client.post("/api/recruitment-bookmarks/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        bookmark_count = RecruitmentBookmarks.objects.filter(recruitment_id=recruitment).count()
        self.assertEqual(bookmark_count, 2)
