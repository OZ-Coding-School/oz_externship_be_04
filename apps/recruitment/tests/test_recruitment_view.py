from datetime import timedelta
from uuid import uuid4

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.recruitment.models import Recruitment, Tag
from apps.study_groups.models import StudyGroup
from apps.users.models import User


class TestDataFactory:
    """테스트 데이터 생성 팩토리"""

    @staticmethod
    def create_user(email="test@test.com", nickname="테스터", password="testpass123"):
        """테스트 사용자 생성"""
        return User.objects.create_user(email=email, password=password, nickname=nickname)

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
        study_group,
        author,
        title="테스트 공고",
        content="테스트 내용입니다.",
        expected_headcount=3,
        days_until_close=7,
        is_closed=False,
        views_count=0,
    ):
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
    def create_tag(name):
        """테스트 태그 생성"""
        return Tag.objects.create(name=name)

    @staticmethod
    def get_valid_recruitment_data(study_group_id, tag_ids=None):
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

    def setUp(self):
        """공통 setUp"""
        self.client = APIClient()
        self.factory = TestDataFactory()

        self.user = self.factory.create_user()
        self.other_user = self.factory.create_user(email="other@test.com", nickname="다른사람")
        self.study_group = self.factory.create_study_group()

        self.tag1 = self.factory.create_tag("Python")
        self.tag2 = self.factory.create_tag("Django")

    def authenticate(self, user=None):
        """사용자 인증"""
        user = user or self.user
        self.client.force_authenticate(user=user)

    def create_recruitment(self, **kwargs):
        """테스트용 공고 생성 헬퍼"""
        defaults = {"study_group": self.study_group, "author": self.user}
        defaults.update(kwargs)
        return self.factory.create_recruitment(**defaults)


class RecruitmentCreateViewTest(BaseRecruitmentTestCase):
    """공고 작성 테스트"""

    def test_create_recruitment_success(self):
        """공고 작성 성공"""
        self.authenticate()
        data = self.factory.get_valid_recruitment_data(self.study_group.id, [self.tag1.id, self.tag2.id])

        response = self.client.post("/api/recruitments/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["detail"], "공고가 작성되었습니다.")

        # DB 확인
        recruitment = Recruitment.objects.get(title=data["title"])
        self.assertEqual(recruitment.author, self.user)
        self.assertEqual(recruitment.study_group, self.study_group)
        self.assertEqual(recruitment.recruitment_tags.count(), 2)
        self.assertEqual(recruitment.attachments.count(), 1)
        self.assertEqual(recruitment.images.count(), 1)

    def test_create_recruitment_unauthenticated(self):
        """비인증 사용자 공고 작성 실패"""
        data = self.factory.get_valid_recruitment_data(self.study_group.id)
        response = self.client.post("/api/recruitments/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_recruitment_with_ended_study_group(self):
        """종료된 스터디 그룹으로 공고 작성 실패"""
        ended_group = self.factory.create_study_group(
            name="종료된 스터디", status=StudyGroup.StudyGroupStatusChoices.ENDED
        )

        self.authenticate()
        data = self.factory.get_valid_recruitment_data(ended_group.id)

        response = self.client.post("/api/recruitments/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recruitment_invalid_title_too_short(self):
        """제목이 5자 미만일 때 실패"""
        self.authenticate()
        data = self.factory.get_valid_recruitment_data(self.study_group.id)
        data["title"] = "짧음"

        response = self.client.post("/api/recruitments/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recruitment_invalid_content_too_short(self):
        """내용이 10자 미만일 때 실패"""
        self.authenticate()
        data = self.factory.get_valid_recruitment_data(self.study_group.id)
        data["content"] = "짧음"

        response = self.client.post("/api/recruitments/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RecruitmentListViewTest(BaseRecruitmentTestCase):
    """공고 목록 조회 테스트"""

    def setUp(self):
        super().setUp()
        for i in range(15):
            self.create_recruitment(title=f"테스트 공고 {i+1}")

    def test_list_recruitments_success(self):
        """공고 목록 조회 성공"""
        response = self.client.get("/api/recruitments/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 15)

    def test_list_recruitments_pagination(self):
        """페이지네이션 테스트"""
        response = self.client.get("/api/recruitments/?page=1&size=10")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data["next"])

    def test_list_recruitments_search(self):
        """검색 기능 테스트"""
        self.create_recruitment(title="Django 스터디원 모집", content="Django 백엔드 개발자 모집합니다.")

        response = self.client.get("/api/recruitments/?search=Django")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_list_recruitments_sorting_by_views(self):
        """조회수 순 정렬 테스트"""
        high_views = self.create_recruitment(title="인기 공고", views_count=100)

        response = self.client.get("/api/recruitments/?sort=most_views")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["uuid"], str(high_views.uuid))

    def test_list_recruitments_excludes_closed(self):
        """마감된 공고는 목록에서 제외"""
        self.create_recruitment(title="마감된 공고", is_closed=True)

        response = self.client.get("/api/recruitments/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 15)  # 마감된 공고 제외


class RecruitmentDetailViewTest(BaseRecruitmentTestCase):
    """공고 상세 조회 테스트"""

    def setUp(self):
        super().setUp()
        self.recruitment = self.create_recruitment()

    def test_detail_recruitment_success(self):
        """공고 상세 조회 성공"""
        response = self.client.get(f"/api/recruitments/{self.recruitment.uuid}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.recruitment.title)
        self.assertIn("content", response.data)
        self.assertIn("lectures", response.data)

    def test_detail_recruitment_increases_view_count(self):
        """조회수 증가 확인"""
        initial_views = self.recruitment.views_count

        self.client.get(f"/api/recruitments/{self.recruitment.uuid}/")
        self.recruitment.refresh_from_db()

        self.assertEqual(self.recruitment.views_count, initial_views + 1)

    def test_detail_recruitment_not_found(self):
        """존재하지 않는 공고 조회 시 404"""
        fake_uuid = uuid4()
        response = self.client.get(f"/api/recruitments/{fake_uuid}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RecruitmentUpdateViewTest(BaseRecruitmentTestCase):
    """공고 수정 테스트"""

    def setUp(self):
        super().setUp()
        self.recruitment = self.create_recruitment(title="원본 제목입니다")

    def test_update_recruitment_success(self):
        """공고 수정 성공"""
        self.authenticate()
        data = {"title": "수정된 제목입니다"}

        response = self.client.patch(f"/api/recruitments/{self.recruitment.uuid}/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "수정된 제목입니다")

    def test_update_recruitment_unauthorized(self):
        """작성자가 아닌 사용자 수정 실패"""
        self.authenticate(self.other_user)
        data = {"title": "수정 시도"}

        response = self.client.patch(f"/api/recruitments/{self.recruitment.uuid}/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("권한", response.data["error_detail"])

    def test_update_closed_recruitment_fails(self):
        """마감된 공고 수정 실패"""
        self.recruitment.is_closed = True
        self.recruitment.save()

        self.authenticate()
        data = {"title": "수정 시도"}

        response = self.client.patch(f"/api/recruitments/{self.recruitment.uuid}/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("마감", response.data["error_detail"])

    def test_update_recruitment_partial(self):
        """부분 수정 (PATCH) 테스트"""
        self.authenticate()
        original_content = self.recruitment.content
        data = {"title": "제목만 수정"}

        response = self.client.patch(f"/api/recruitments/{self.recruitment.uuid}/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recruitment.refresh_from_db()
        self.assertEqual(self.recruitment.title, "제목만 수정")
        self.assertEqual(self.recruitment.content, original_content)


class RecruitmentDeleteViewTest(BaseRecruitmentTestCase):
    """공고 삭제 테스트"""

    def setUp(self):
        super().setUp()
        self.recruitment = self.create_recruitment()

    def test_delete_recruitment_success(self):
        """공고 삭제(Soft Delete) 성공"""
        self.authenticate()

        response = self.client.delete(f"/api/recruitments/{self.recruitment.uuid}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "공고가 삭제되었습니다.")

        self.recruitment.refresh_from_db()
        self.assertTrue(self.recruitment.is_closed)

    def test_delete_recruitment_unauthorized(self):
        """작성자가 아닌 사용자 삭제 실패"""
        self.authenticate(self.other_user)

        response = self.client.delete(f"/api/recruitments/{self.recruitment.uuid}/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_already_closed_recruitment_fails(self):
        """이미 마감된 공고 삭제 실패"""
        self.recruitment.is_closed = True
        self.recruitment.save()

        self.authenticate()

        response = self.client.delete(f"/api/recruitments/{self.recruitment.uuid}/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("이미 마감", response.data["error_detail"])

    def test_delete_recruitment_not_found(self):
        """존재하지 않는 공고 삭제 시 404"""
        self.authenticate()
        fake_uuid = uuid4()

        response = self.client.delete(f"/api/recruitments/{fake_uuid}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RecruitmentMineViewTest(BaseRecruitmentTestCase):
    """내가 작성한 공고 목록 테스트"""

    def setUp(self):
        super().setUp()

        for i in range(5):
            self.create_recruitment(title=f"내 공고 {i+1}")

        for i in range(3):
            self.create_recruitment(author=self.other_user, title=f"다른 사람 공고 {i+1}")

    def test_mine_recruitments_success(self):
        """내 공고 목록 조회 성공"""
        self.authenticate()

        response = self.client.get("/api/recruitments/mine/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)

    def test_mine_recruitments_unauthenticated(self):
        """비인증 사용자는 접근 불가"""
        response = self.client.get("/api/recruitments/mine/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_mine_recruitments_filter_by_is_closed_true(self):
        """마감된 공고만 필터링"""
        recruitment = Recruitment.objects.filter(author=self.user).first()
        recruitment.is_closed = True
        recruitment.save()

        self.authenticate()
        response = self.client.get("/api/recruitments/mine/?is_closed=true")

        self.assertEqual(response.data["count"], 1)

    def test_mine_recruitments_filter_by_is_closed_false(self):
        """진행 중인 공고만 필터링"""
        recruitment = Recruitment.objects.filter(author=self.user).first()
        recruitment.is_closed = True
        recruitment.save()

        self.authenticate()
        response = self.client.get("/api/recruitments/mine/?is_closed=false")

        self.assertEqual(response.data["count"], 4)

    def test_mine_recruitments_search(self):
        """내 공고에서 검색"""
        self.authenticate()

        response = self.client.get("/api/recruitments/mine/?search=공고 1")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)


class HelperFunctionsTest(BaseRecruitmentTestCase):
    """헬퍼 함수 단위 테스트"""

    def setUp(self):
        super().setUp()
        self.recruitment = self.create_recruitment()

    def test_check_author_permission_authorized(self):
        """작성자 권한 확인 - 작성자인 경우"""
        from apps.recruitment.views.recruitment_view import check_author_permission

        result = check_author_permission(self.recruitment, self.user)
        self.assertIsNone(result)

    def test_check_author_permission_unauthorized(self):
        """작성자 권한 확인 - 작성자가 아닌 경우"""
        from apps.recruitment.views.recruitment_view import check_author_permission

        result = check_author_permission(self.recruitment, self.other_user)
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)

    def test_save_recruitment_relations_bulk_create(self):
        """bulk_create 최적화 확인"""
        from apps.recruitment.views.recruitment_view import save_recruitment_relations

        tags = [self.tag1, self.tag2]
        files = [
            {"file_name": "file1.pdf", "file_url": "https://example.com/file1.pdf"},
            {"file_name": "file2.pdf", "file_url": "https://example.com/file2.pdf"},
        ]
        image_urls = ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]

        with self.assertNumQueries(3):
            save_recruitment_relations(self.recruitment, tags, files, image_urls)

        self.assertEqual(self.recruitment.recruitment_tags.count(), 2)
        self.assertEqual(self.recruitment.attachments.count(), 2)
        self.assertEqual(self.recruitment.images.count(), 2)

    def test_apply_search_filter(self):
        """검색 필터 함수 테스트"""
        from apps.recruitment.views.recruitment_view import (
            apply_search_filter,
            get_base_recruitment_queryset,
        )

        self.create_recruitment(title="Django 튜토리얼")
        self.create_recruitment(title="React 강의")

        queryset = get_base_recruitment_queryset()
        filtered = apply_search_filter(queryset, "Django")

        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().title, "Django 튜토리얼")

    def test_apply_sorting_latest(self):
        """최신순 정렬 테스트"""
        from apps.recruitment.views.recruitment_view import (
            apply_sorting,
            get_base_recruitment_queryset,
        )

        old = self.create_recruitment(title="오래된 공고")
        new = self.create_recruitment(title="최신 공고")

        queryset = get_base_recruitment_queryset()
        sorted_qs = apply_sorting(queryset, "latest")

        self.assertEqual(sorted_qs.first().title, "최신 공고")

    def test_apply_sorting_most_views(self):
        """조회수 순 정렬 테스트"""
        from apps.recruitment.views.recruitment_view import (
            apply_sorting,
            get_base_recruitment_queryset,
        )

        low = self.create_recruitment(title="조회수 낮음", views_count=10)
        high = self.create_recruitment(title="조회수 높음", views_count=100)

        queryset = get_base_recruitment_queryset()
        sorted_qs = apply_sorting(queryset, "most_views")

        self.assertEqual(sorted_qs.first().title, "조회수 높음")
