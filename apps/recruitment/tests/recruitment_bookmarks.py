from datetime import timedelta
from uuid import uuid4

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.recruitment.models import Recruitment, RecruitmentBookmarks, Tag
from apps.study_groups.models import StudyGroup
from apps.users.models import User


class BookmarkTestDataFactory:
    """북마크 테스트 데이터 생성 팩토리"""

    @staticmethod
    def create_user(email="test@test.com", nickname="테스터", password="testpass123"):
        """테스트 사용자 생성"""
        user = User.objects.create_user(email=email, password=password, nickname=nickname)
        if hasattr(user, "name"):
            user.name = nickname
        if hasattr(user, "phone_number"):
            user.phone_number = "01012345678"
        if hasattr(user, "birthday"):
            user.birthday = "1990-01-01"
        if hasattr(user, "gender"):
            user.gender = "M"
        user.save()
        return user

    @staticmethod
    def create_study_group(name="테스트 스터디", status=StudyGroup.StudyGroupStatusChoices.ONGOING, days_until_end=30):
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
        study_group, author, title="테스트 공고", content="테스트 내용입니다.", expected_headcount=3, days_until_close=7
    ):
        """테스트 공고 생성"""
        return Recruitment.objects.create(
            study_group=study_group,
            author=author,
            title=title,
            content=content,
            expected_headcount=expected_headcount,
            close_at=timezone.now() + timedelta(days=days_until_close),
            estimated_fee=50000,
            is_closed=False,
        )

    @staticmethod
    def create_bookmark(user, recruitment):
        """테스트 북마크 생성"""
        return RecruitmentBookmarks.objects.create(user_id=user, recruitment_id=recruitment)


class BaseBookmarkTestCase(TestCase):
    """북마크 테스트 베이스 클래스"""

    def setUp(self):
        """공통 setUp"""
        self.client = APIClient()
        self.factory = BookmarkTestDataFactory()

        self.user = self.factory.create_user()
        self.other_user = self.factory.create_user(email="other@test.com", nickname="다른사람")

        self.study_group = self.factory.create_study_group()

        self.recruitment1 = self.factory.create_recruitment(
            study_group=self.study_group, author=self.user, title="Python 스터디 모집"
        )
        self.recruitment2 = self.factory.create_recruitment(
            study_group=self.study_group, author=self.user, title="Django 스터디 모집"
        )
        self.recruitment3 = self.factory.create_recruitment(
            study_group=self.study_group, author=self.user, title="React 스터디 모집"
        )

    def authenticate(self, user=None):
        """사용자 인증"""
        user = user or self.user
        self.client.force_authenticate(user=user)

    def create_bookmark(self, user=None, recruitment=None):
        """북마크 생성 헬퍼"""
        user = user or self.user
        recruitment = recruitment or self.recruitment1
        return self.factory.create_bookmark(user, recruitment)


class RecruitmentBookmarkListTest(BaseBookmarkTestCase):
    """북마크 목록 조회 테스트"""

    def setUp(self):
        super().setUp()
        self.bookmark1 = self.create_bookmark(recruitment=self.recruitment1)
        self.bookmark2 = self.create_bookmark(recruitment=self.recruitment2)
        self.bookmark3 = self.create_bookmark(recruitment=self.recruitment3)

    def test_list_bookmarks_success(self):
        """북마크 목록 조회 성공"""
        self.authenticate()

        response = self.client.get("/api/recruitment-bookmarks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 3)

    def test_list_bookmarks_unauthenticated(self):
        """비인증 사용자는 접근 불가"""
        response = self.client.get("/api/recruitment-bookmarks/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_bookmarks_with_search(self):
        """검색 기능 테스트"""
        self.authenticate()

        response = self.client.get("/api/recruitment-bookmarks/?q=Python")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(any("Python" in r.get("title", "") for r in results))

    def test_list_bookmarks_empty_for_other_user(self):
        """다른 사용자는 내 북마크를 볼 수 없음"""
        self.authenticate(self.other_user)

        response = self.client.get("/api/recruitment-bookmarks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_list_bookmarks_pagination(self):
        """페이지네이션 테스트"""
        self.authenticate()
        for i in range(10):
            recruitment = self.factory.create_recruitment(
                study_group=self.study_group, author=self.user, title=f"추가 공고 {i+1}"
            )
            self.create_bookmark(recruitment=recruitment)

        response = self.client.get("/api/recruitment-bookmarks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("next", response.data)  # 다음 페이지 존재


class RecruitmentBookmarkCreateTest(BaseBookmarkTestCase):
    """북마크 추가 테스트"""

    def test_create_bookmark_success(self):
        """북마크 추가 성공"""
        self.authenticate()
        data = {"recruitment_uuid": str(self.recruitment1.uuid)}

        response = self.client.post("/api/recruitment-bookmarks/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["detail"], "북마크가 추가되었습니다.")
        self.assertTrue(
            RecruitmentBookmarks.objects.filter(user_id=self.user, recruitment_id=self.recruitment1).exists()
        )

    def test_create_bookmark_duplicate(self):
        """중복 북마크 추가 실패"""
        self.authenticate()
        self.create_bookmark(recruitment=self.recruitment1)

        data = {"recruitment_uuid": str(self.recruitment1.uuid)}
        response = self.client.post("/api/recruitment-bookmarks/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("이미 북마크", response.data["error_detail"])

    def test_create_bookmark_unauthenticated(self):
        """비인증 사용자 북마크 추가 실패"""
        data = {"recruitment_uuid": str(self.recruitment1.uuid)}

        response = self.client.post("/api/recruitment-bookmarks/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_bookmark_invalid_uuid(self):
        """존재하지 않는 공고 UUID"""
        self.authenticate()
        fake_uuid = uuid4()
        data = {"recruitment_uuid": str(fake_uuid)}

        response = self.client.post("/api/recruitment-bookmarks/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_bookmark_invalid_uuid_format(self):
        """잘못된 UUID 형식"""
        self.authenticate()
        data = {"recruitment_uuid": "invalid-uuid"}

        response = self.client.post("/api/recruitment-bookmarks/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RecruitmentBookmarkDeleteTest(BaseBookmarkTestCase):
    """북마크 삭제 테스트"""

    def setUp(self):
        super().setUp()
        self.bookmark = self.create_bookmark(recruitment=self.recruitment1)

    def test_delete_bookmark_success(self):
        """북마크 삭제 성공"""
        self.authenticate()
        data = {"recruitment_uuid": str(self.recruitment1.uuid)}

        response = self.client.delete("/api/recruitment-bookmarks/delete/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "북마크가 삭제되었습니다.")

        self.assertFalse(
            RecruitmentBookmarks.objects.filter(user_id=self.user, recruitment_id=self.recruitment1).exists()
        )

    def test_delete_bookmark_not_found(self):
        """존재하지 않는 북마크 삭제 실패"""
        self.authenticate()
        data = {"recruitment_uuid": str(self.recruitment2.uuid)}

        response = self.client.delete("/api/recruitment-bookmarks/delete/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("찾을 수 없습니다", response.data["error_detail"])

    def test_delete_bookmark_unauthenticated(self):
        """비인증 사용자 북마크 삭제 실패"""
        data = {"recruitment_uuid": str(self.recruitment1.uuid)}

        response = self.client.delete("/api/recruitment-bookmarks/delete/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_other_user_bookmark(self):
        """다른 사용자의 북마크 삭제 불가"""
        other_bookmark = self.create_bookmark(user=self.other_user, recruitment=self.recruitment2)
        self.authenticate(self.user)
        data = {"recruitment_uuid": str(self.recruitment2.uuid)}

        response = self.client.delete("/api/recruitment-bookmarks/delete/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertTrue(
            RecruitmentBookmarks.objects.filter(user_id=self.other_user, recruitment_id=self.recruitment2).exists()
        )


class BookmarkSerializerTest(BaseBookmarkTestCase):
    """시리얼라이저 테스트"""

    def setUp(self):
        super().setUp()
        self.bookmark = self.create_bookmark(recruitment=self.recruitment1)

    def test_bookmark_card_serializer_fields(self):
        """북마크 카드 시리얼라이저 필드 확인"""
        from apps.recruitment.serializers.recruitment_bookmarks import (
            RecruitmentBookmarkCardSerializer,
        )

        serializer = RecruitmentBookmarkCardSerializer(self.bookmark)
        data = serializer.data

        self.assertIn("id", data)
        self.assertIn("recruitment_uuid", data)
        self.assertIn("title", data)
        self.assertIn("thumbnail_img_url", data)
        self.assertIn("expected_headcount", data)
        self.assertIn("lectures", data)
        self.assertIn("tags", data)
        self.assertIn("close_at", data)
        self.assertIn("views_count", data)
        self.assertIn("bookmark_count", data)

    def test_bookmark_create_serializer_validation(self):
        """생성 시리얼라이저 유효성 검증"""
        from apps.recruitment.serializers.recruitment_bookmarks import (
            RecruitmentBookmarkCreateSerializer,
        )

        serializer = RecruitmentBookmarkCreateSerializer(data={"recruitment_uuid": str(self.recruitment1.uuid)})
        self.assertTrue(serializer.is_valid())

        serializer = RecruitmentBookmarkCreateSerializer(data={"recruitment_uuid": "invalid-uuid"})
        self.assertFalse(serializer.is_valid())

    def test_thumbnail_url_with_image(self):
        """이미지가 있는 경우 썸네일 URL"""
        from apps.recruitment.models import RecruitmentImage
        from apps.recruitment.serializers.recruitment_bookmarks import (
            RecruitmentBookmarkCardSerializer,
        )

        RecruitmentImage.objects.create(recruitment=self.recruitment1, img_url="https://example.com/image.jpg")

        serializer = RecruitmentBookmarkCardSerializer(self.bookmark)
        data = serializer.data

        self.assertEqual(data["thumbnail_img_url"], "https://example.com/image.jpg")


class BookmarkQueryOptimizationTest(BaseBookmarkTestCase):
    """쿼리 최적화 테스트"""

    def setUp(self):
        super().setUp()
        for i in range(5):
            recruitment = self.factory.create_recruitment(
                study_group=self.study_group, author=self.user, title=f"공고 {i+1}"
            )
            self.create_bookmark(recruitment=recruitment)

    def test_list_query_optimization(self):
        """목록 조회 쿼리 최적화 확인"""
        self.authenticate()

        with self.assertNumQueries(4):
            response = self.client.get("/api/recruitment-bookmarks/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
