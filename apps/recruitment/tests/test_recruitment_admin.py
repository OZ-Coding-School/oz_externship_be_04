import uuid
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.application.models import Application, ApplicationStatus
from apps.lectures.models import Category, CrawledLecture, LectureCategory
from apps.recruitment.models import (
    Recruitment,
    RecruitmentAttachment,
    RecruitmentBookmarks,
    RecruitmentTag,
    Tag,
)
from apps.study_groups.models import StudyGroup, StudyLecture
from apps.users.models.users import User


class AdminRecruitmentAPITestCase(APITestCase):
    """관리자용 구인 공고 API 테스트"""

    def setUp(self) -> None:

        # 1. 유저 생성
        self.admin_user = User.objects.create(
            email="admin@test.com",
            password="password123",
            nickname="Admin",
            name="관리자",
            phone_number="01011112222",
            gender="M",
            birthday="2000-01-01",
            profile_img_url="http://example.com/admin.png",
            is_staff=True,
            is_superuser=True,
        )

        self.user1 = User.objects.create(
            email="user1@test.com",
            password="password123",
            nickname="User1",
            name="사용자1",
            phone_number="01033334444",
            gender="F",
            birthday="2001-01-01",
            profile_img_url="http://example.com/user1.png",
        )

        self.user2 = User.objects.create(
            email="user2@test.com",
            password="password123",
            nickname="User2",
            name="사용자2",
            phone_number="01055556666",
            gender="M",
            birthday="2002-01-01",
            profile_img_url="http://example.com/user2.png",
        )

        # 2. 스터디 그룹 생성
        self.study_group_1 = StudyGroup.objects.create(
            name="Python 스터디",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=30),
        )
        self.study_group_2 = StudyGroup.objects.create(
            name="Django 프로젝트",
            max_headcount=3,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=60),
        )

        # 3. 강의 & 카테고리 생성
        category_1 = Category.objects.create(name="개발")
        category_2 = Category.objects.create(name="백엔드")

        self.lecture_1 = CrawledLecture.objects.create(
            external_id=1,
            title="파이썬 기초",
            instructor="김강사",
            average_rating=4.50,
            total_class_time=10,
            difficulty="EASY",
            description="기초 강의",
            platform="INFLEARN",
            url_link="http://link1.com",
        )

        self.lecture_2 = CrawledLecture.objects.create(
            external_id=2,
            title="DRF 실전",
            instructor="박강사",
            average_rating=4.00,
            total_class_time=20,
            difficulty="NORMAL",
            description="실전 강의",
            platform="UDEMY",
            url_link="http://link2.com",
        )

        LectureCategory.objects.create(lecture=self.lecture_1, category=category_1)
        LectureCategory.objects.create(lecture=self.lecture_2, category=category_2)

        # 스터디-강의 연결
        StudyLecture.objects.create(study_group=self.study_group_1, lecture=self.lecture_1)
        StudyLecture.objects.create(study_group=self.study_group_2, lecture=self.lecture_2)

        # 4. 태그 생성
        self.tag_python = Tag.objects.create(name="Python")
        self.tag_django = Tag.objects.create(name="Django")
        self.tag_backend = Tag.objects.create(name="백엔드")

        # 5. 공고 생성
        self.recruitment_1 = Recruitment.objects.create(
            study_group=self.study_group_1,
            author=self.user1,
            title="파이썬 스터디원 모집",
            content="함께 공부하실 분",
            expected_headcount=5,
            estimated_fee=100000,
            close_at=timezone.now() + timedelta(days=10),
            views_count=50,
            is_closed=False,
        )

        self.recruitment_2 = Recruitment.objects.create(
            study_group=self.study_group_2,
            author=self.user2,
            title="Django 프로젝트 참여자 구함",
            content="포트폴리오용 프로젝트",
            expected_headcount=3,
            estimated_fee=50000,
            close_at=timezone.now() - timedelta(days=1),
            views_count=100,
            is_closed=True,
        )

        self.recruitment_3 = Recruitment.objects.create(
            study_group=self.study_group_1,
            author=self.user1,
            title="새로운 파이썬 스터디",
            content="신규 모집 공고",
            expected_headcount=4,
            estimated_fee=200000,
            close_at=timezone.now() + timedelta(days=5),
            views_count=10,
            is_closed=False,
        )

        # 태그 연결
        RecruitmentTag.objects.create(recruitment=self.recruitment_1, tag=self.tag_python)
        RecruitmentTag.objects.create(recruitment=self.recruitment_1, tag=self.tag_backend)
        RecruitmentTag.objects.create(recruitment=self.recruitment_2, tag=self.tag_django)

        # 북마크
        RecruitmentBookmarks.objects.create(recruitment_id=self.recruitment_1, user_id=self.user1)
        RecruitmentBookmarks.objects.create(recruitment_id=self.recruitment_1, user_id=self.user2)
        RecruitmentBookmarks.objects.create(recruitment_id=self.recruitment_3, user_id=self.user1)

        # 첨부파일
        RecruitmentAttachment.objects.create(
            recruitment=self.recruitment_1,
            file_name="file1.pdf",
            file_url="http://file.url/1",
        )

        # 지원서
        Application.objects.create(
            recruitment=self.recruitment_1,
            applicant=self.user2,
            objective="파이썬 실력 향상",
            motivation="함께 성장하고 싶습니다.",
            self_introduction="3학년 재학생",
            available_time="주 2회",
            status=ApplicationStatus.PENDING,
        )

        Application.objects.create(
            recruitment=self.recruitment_1,
            applicant=self.user1,
            objective="리더 역할 수행",
            motivation="모임의 질을 높이고 싶습니다.",
            self_introduction="경력 5년",
            available_time="조율 가능",
            status=ApplicationStatus.ACCEPTED,
        )

        # 인증
        self.client.force_authenticate(user=self.admin_user)

        # URL 초기화
        self.list_url = "/api/v1/admin/recruitments"
        self.detail_url_1 = f"/api/v1/admin/recruitments/{self.recruitment_1.id}"

        # 1. 구인 공고 목록 조회 API 테스트 (필터링 및 정렬)

    def test_admin_only_access(self) -> None:
        """비관리자는 접근할 수 없습니다. (권한 테스트)"""

        # 비로그인
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 일반 사용자 로그인
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 관리자 로그인
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_all_recruitments_default_sort(self) -> None:
        """기본 정렬(-created_at, 최신순)로 모든 공고를 조회합니다."""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

        # 최신순: recruitment_3 -> recruitment_2 -> recruitment_1
        results = response.data["results"]
        self.assertEqual(results[0]["id"], self.recruitment_3.id)
        self.assertEqual(results[1]["id"], self.recruitment_2.id)
        self.assertEqual(results[2]["id"], self.recruitment_1.id)

    def test_search_by_title(self) -> None:
        """제목으로 공고를 검색합니다."""
        search_url = f"{self.list_url}?search=파이썬"
        response = self.client.get(search_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        titles = [r["title"] for r in response.data["results"]]
        self.assertIn("파이썬 스터디원 모집", titles)
        self.assertIn("새로운 파이썬 스터디", titles)

    def test_filter_by_open_status(self) -> None:
        """모집중(status=open)인 공고만 필터링 합니다."""
        open_url = f"{self.list_url}?is_closed=false"
        response = self.client.get(open_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        ids = [r["id"] for r in response.data["results"]]
        self.assertIn(self.recruitment_1.id, ids)
        self.assertIn(self.recruitment_3.id, ids)
        self.assertNotIn(self.recruitment_2.id, ids)

    def test_filter_by_closed_status(self) -> None:
        """마감(status=closed)된 공고만 필터링합니다."""
        closed_url = f"{self.list_url}?is_closed=true"
        response = self.client.get(closed_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.recruitment_2.id)

    def test_filter_by_multiple_tags(self) -> None:
        """다중 태그 중 하나라도 포함하는 공고를 필터링합니다."""
        tag_url = f"{self.list_url}?tags=Django,Python,미사용태그"
        response = self.client.get(tag_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        ids = [r["id"] for r in response.data["results"]]
        self.assertIn(self.recruitment_1.id, ids)  # Python 태그 포함
        self.assertIn(self.recruitment_2.id, ids)  # Django 태그 포함

    def test_sort_by_views(self) -> None:
        """조회수(sort=views) 내림차순으로 정렬합니다."""
        # views_count: 1(50), 2(100), 3(10)
        sort_url = f"{self.list_url}?sort=views"
        response = self.client.get(sort_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(results[0]["id"], self.recruitment_2.id)  # 100
        self.assertEqual(results[1]["id"], self.recruitment_1.id)  # 50
        self.assertEqual(results[2]["id"], self.recruitment_3.id)  # 10

    def test_sort_by_bookmarked(self) -> None:
        """북마크 수(sort=bookmarked) 내림차순으로 정렬합니다."""
        # 북마크 수: 1(2), 2(0), 3(1)
        sort_url = f"{self.list_url}?sort=bookmarked"
        response = self.client.get(sort_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(results[0]["id"], self.recruitment_1.id)  # 2개
        self.assertEqual(results[1]["id"], self.recruitment_3.id)  # 1개
        self.assertEqual(results[2]["id"], self.recruitment_2.id)  # 0개

    def test_pagination(self) -> None:
        """페이지네이션이 올바르게 작동하는지 확인합니다."""
        paginated_url = f"{self.list_url}?page=1&page_size=2"
        response = self.client.get(paginated_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 2)
        # 페이지 1에는 최신순 2개 공고: recruitment_3, recruitment_2
        results = response.data["results"]
        self.assertEqual(results[0]["id"], self.recruitment_3.id)
        self.assertEqual(results[1]["id"], self.recruitment_2.id)

        # 2. 구인 공고 상세 조회 API 테스트

    def test_retrieve_recruitment_detail_success(self) -> None:
        """특정 구인 공고의 상세 정보를 성공적으로 조회합니다."""
        response = self.client.get(self.detail_url_1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # 주요 정보 확인
        self.assertEqual(data["id"], self.recruitment_1.id)
        self.assertEqual(data["title"], "파이썬 스터디원 모집")
        self.assertEqual(data["bookmark_count"], 2)

        # 연관 정보 확인
        tag_names = [t["name"] for t in data["tags"]]
        self.assertIn("Python", tag_names)
        self.assertEqual(data["lectures"][0]["title"], "파이썬 기초")
        self.assertEqual(data["files"][0]["file_name"], "file1.pdf")
        self.assertEqual(len(data["applications"]), 2)

    def test_retrieve_nonexistent_recruitment(self) -> None:
        """존재하지 않는 구인공고 ID로 조회 시 404를 반환합니다."""
        non_existent_id = 9999  # 존재하지 않는 정수 ID
        detail_url = f"/api/v1/admin/recruitments/{non_existent_id}"
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("해당 구인공고를 찾을 수 없습니다.", response.data["error_detail"])

        # 3. 구인 공고 삭제 API 테스트

    def test_admin_can_delete_recruitment(self) -> None:
        """관리자는 구인공고를 삭제할 수 있습니다. 삭제 후 관련 지원 내역도 삭제됩니다."""

        # 다른 테스트와의 격리를 위해 삭제 URL을 테스트 내부에 생성.
        delete_url = f"/api/v1/admin/recruitments/{self.recruitment_1.id}"

        # 삭제 전 존재 여부 확인
        self.assertTrue(Recruitment.objects.filter(id=self.recruitment_1.id).exists())
        self.assertTrue(Application.objects.filter(recruitment_id=self.recruitment_1.id).exists())

        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 삭제 후 확인
        self.assertFalse(Recruitment.objects.filter(id=self.recruitment_1.id).exists())
        self.assertFalse(Application.objects.filter(recruitment_id=self.recruitment_1.id).exists())

    def test_delete_nonexistent_recruitment(self) -> None:
        """존재하지 않는 구인공고를 삭제 시 404 반환"""
        non_existent_id = 9999  # 존재하지 않는 정수 ID
        delete_url = f"/api/v1/admin/recruitments/{non_existent_id}"
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
