from datetime import date, timedelta
from typing import Any

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.recruitment.models import Recruitment, RecruitmentBookmarks
from apps.study_groups.models import StudyGroup
from apps.users.models import User


class RecruitmentBookmarkAPITestCase(APITestCase):
    """공통 북마크 테스트 베이스 클래스"""

    def setUp(self) -> None:
        self.user = self._create_user(email="test@test.com", nickname="테스터")
        self.other_user = self._create_user(email="other@test.com", nickname="다른사람")
        self.study_group = self._create_study_group()
        self.client.force_authenticate(user=self.user)

    def _create_user(
        self,
        email: str,
        nickname: str,
        password: str = "testpass123",
    ) -> User:
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

    def _create_study_group(
        self,
        name: str = "테스트 스터디",
        status: str = StudyGroup.StudyGroupStatusChoices.ONGOING,
    ) -> StudyGroup:
        return StudyGroup.objects.create(
            name=name,
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=30),
            status=status,
        )

    def _create_recruitment(
        self,
        study_group: StudyGroup | None = None,
        author: User | None = None,
        title: str = "테스트 공고",
        **kwargs: Any,
    ) -> Recruitment:
        study_group = study_group or self.study_group
        author = author or self.user
        defaults = {
            "content": "테스트 내용입니다.",
            "estimated_fee": 50000,
            "expected_headcount": 3,
            "close_at": timezone.now() + timedelta(days=7),
            "is_closed": False,
        }
        defaults.update(kwargs)
        return Recruitment.objects.create(study_group=study_group, author=author, title=title, **defaults)

    def _create_bookmark(self, user: User, recruitment: Recruitment) -> RecruitmentBookmarks:
        return RecruitmentBookmarks.objects.create(user_id=user, recruitment_id=recruitment)

    def _create_multiple_bookmarks(
        self, count: int, title_prefix: str = "공고", **kwargs: Any
    ) -> list[RecruitmentBookmarks]:
        bookmarks = []
        for i in range(count):
            recruitment = self._create_recruitment(title=f"{title_prefix} {i+1}", **kwargs)
            bookmarks.append(self._create_bookmark(self.user, recruitment))
        return bookmarks


class RecruitmentBookmarkListCreateViewTest(RecruitmentBookmarkAPITestCase):
    """북마크 목록 조회 및 추가 테스트"""

    def setUp(self) -> None:
        super().setUp()
        self.recruitment = self._create_recruitment(title="북마크할 공고")

    def test_create_bookmark_success(self) -> None:
        """북마크 추가 성공"""
        url = reverse("recruitment-bookmark-list-create")
        data = {"recruitment_uuid": str(self.recruitment.uuid)}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "북마크가 추가되었습니다.")
        self.assertTrue(
            RecruitmentBookmarks.objects.filter(user_id_id=self.user.id, recruitment_id_id=self.recruitment.id).exists()
        )

    def test_create_bookmark_unauthenticated(self) -> None:
        """비인증 사용자 북마크 추가 불가"""
        self.client.force_authenticate(user=None)
        url = reverse("recruitment-bookmark-list-create")
        data = {"recruitment_uuid": str(self.recruitment.uuid)}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_bookmark_duplicate(self) -> None:
        """중복 북마크 추가 실패"""
        self._create_bookmark(self.user, self.recruitment)

        url = reverse("recruitment-bookmark-list-create")
        data = {"recruitment_uuid": str(self.recruitment.uuid)}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("이미 북마크한 공고입니다", response.data["error_detail"])

    def test_create_bookmark_recruitment_not_found(self) -> None:
        """존재하지 않는 공고 북마크 실패"""
        url = reverse("recruitment-bookmark-list-create")
        data = {"recruitment_uuid": "00000000-0000-0000-0000-000000000000"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_bookmarks_success(self) -> None:
        """북마크 목록 조회 성공"""
        self._create_multiple_bookmarks(15)
        url = reverse("recruitment-bookmark-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)

    def test_list_bookmarks_unauthenticated(self) -> None:
        """비인증 사용자 목록 조회 불가"""
        self.client.force_authenticate(user=None)
        url = reverse("recruitment-bookmark-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_bookmarks_only_own_bookmarks(self) -> None:
        """자신의 북마크만 조회됨"""
        self._create_multiple_bookmarks(5)

        for i in range(3):
            recruitment = self._create_recruitment(author=self.other_user, title=f"다른 사람 공고 {i+1}")
            self._create_bookmark(self.other_user, recruitment)

        url = reverse("recruitment-bookmark-list-create")
        response = self.client.get(url, {"page_size": "20"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)

    def test_list_bookmarks_search(self) -> None:
        """검색 기능 동작 확인"""
        recruitment = self._create_recruitment(title="Django 백엔드 스터디")
        self._create_bookmark(self.user, recruitment)
        self._create_multiple_bookmarks(5, title_prefix="React")

        url = reverse("recruitment-bookmark-list-create")
        response = self.client.get(url, {"search": "Django"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_list_bookmarks_cursor_pagination(self) -> None:
        """커서 페이지네이션 동작 확인"""
        self._create_multiple_bookmarks(15)
        url = reverse("recruitment-bookmark-list-create")
        response = self.client.get(url, {"page_size": "10"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("next", response.data)
        self.assertIsNotNone(response.data["next"])


class RecruitmentBookmarkDeleteViewTest(RecruitmentBookmarkAPITestCase):
    """북마크 삭제 테스트"""

    def setUp(self) -> None:
        super().setUp()
        self.recruitment = self._create_recruitment(title="북마크된 공고")
        self.bookmark = self._create_bookmark(self.user, self.recruitment)

    def test_delete_bookmark_success(self) -> None:
        """북마크 삭제 성공"""
        url = reverse("recruitment-bookmark-delete", kwargs={"bookmark_id": self.bookmark.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "북마크가 취소되었습니다.")
        self.assertFalse(RecruitmentBookmarks.objects.filter(id=self.bookmark.id).exists())

    def test_delete_bookmark_unauthenticated(self) -> None:
        """비인증 사용자 삭제 불가"""
        self.client.force_authenticate(user=None)
        url = reverse("recruitment-bookmark-delete", kwargs={"bookmark_id": self.bookmark.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_bookmark_unauthorized(self) -> None:
        """다른 사용자의 북마크 삭제 실패"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("recruitment-bookmark-delete", kwargs={"bookmark_id": self.bookmark.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("권한이 없습니다", response.data["error_detail"])

    def test_delete_bookmark_not_found(self) -> None:
        """존재하지 않는 북마크 삭제 실패"""
        url = reverse("recruitment-bookmark-delete", kwargs={"bookmark_id": 999999})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("북마크 내역을 찾을 수 없습니다", response.data["error_detail"])


class BookmarkIntegrationTest(RecruitmentBookmarkAPITestCase):
    """북마크 통합 시나리오 테스트"""

    def test_bookmark_full_cycle(self) -> None:
        """북마크 생성 → 조회 → 삭제 전체 플로우"""
        recruitment = self._create_recruitment(title="통합 테스트 공고")

        # 1. 북마크 추가
        url = reverse("recruitment-bookmark-list-create")
        data = {"recruitment_uuid": str(recruitment.uuid)}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2. 북마크 목록 조회
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

        # 3. 북마크 삭제
        bookmark = RecruitmentBookmarks.objects.get(user_id_id=self.user.id, recruitment_id_id=recruitment.id)
        url = reverse("recruitment-bookmark-delete", kwargs={"bookmark_id": bookmark.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(RecruitmentBookmarks.objects.filter(id=bookmark.id).exists())

    def test_multiple_users_bookmarking_same_recruitment(self) -> None:
        """여러 사용자가 같은 공고를 북마크"""
        recruitment = self._create_recruitment(title="인기 공고")

        # User1 북마크 추가
        url = reverse("recruitment-bookmark-list-create")
        data = {"recruitment_uuid": str(recruitment.uuid)}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # User2 북마크 추가
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        bookmark_count = RecruitmentBookmarks.objects.filter(recruitment_id_id=recruitment.id).count()
        self.assertEqual(bookmark_count, 2)
