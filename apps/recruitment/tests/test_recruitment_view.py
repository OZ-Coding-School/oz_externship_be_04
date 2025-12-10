from datetime import date, timedelta
from typing import Any

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.recruitment.models import Recruitment, Tag
from apps.study_groups.models import StudyGroup
from apps.users.models import User


class RecruitmentViewAPITestCase(APITestCase):
    """공통 테스트 베이스 클래스"""

    def setUp(self) -> None:
        self.user = self._create_user(email="test@test.com", nickname="테스터")
        self.other_user = self._create_user(email="other@test.com", nickname="다른사람")
        self.study_group = self._create_study_group()
        self.tag1 = Tag.objects.create(name="Python")
        self.tag2 = Tag.objects.create(name="Django")
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
        days_until_end: int = 30,
    ) -> StudyGroup:
        return StudyGroup.objects.create(
            name=name,
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=days_until_end),
            status=status,
        )

    def _create_recruitment(
        self,
        study_group: StudyGroup | None = None,
        author: User | None = None,
        title: str = "테스트 공고",
        content: str = "테스트 내용입니다.",
        is_closed: bool = False,
        **kwargs: Any,
    ) -> Recruitment:
        study_group = study_group or self.study_group
        author = author or self.user
        defaults = {
            "estimated_fee": 50000,
            "expected_headcount": 3,
            "close_at": timezone.now() + timedelta(days=7),
            "is_closed": is_closed,
            "views_count": 0,
        }
        defaults.update(kwargs)
        return Recruitment.objects.create(
            study_group=study_group,
            author=author,
            title=title,
            content=content,
            **defaults,
        )

    def _create_multiple_recruitments(self, count: int, title_prefix: str = "공고", **kwargs: Any) -> list[Recruitment]:
        return [self._create_recruitment(title=f"{title_prefix} {i+1}", **kwargs) for i in range(count)]

    def _get_valid_recruitment_data(
        self, study_group_id: int | None = None, tag_ids: list[int] | None = None
    ) -> dict[str, Any]:
        study_group_id = study_group_id or self.study_group.id
        data = {
            "study_group": study_group_id,
            "title": "테스트 공고 제목",
            "content": "테스트 공고 내용입니다.",
            "estimated_fee": 50000,
            "expected_headcount": 3,
            "close_at": (timezone.now() + timedelta(days=7)).isoformat(),
        }
        if tag_ids:
            data["tags"] = tag_ids
        return data


class RecruitmentListCreateViewTest(RecruitmentViewAPITestCase):
    """공고 목록 조회 및 작성 테스트"""

    def test_create_recruitment_success(self) -> None:
        """공고 작성 성공"""
        url = reverse("recruitment-list-create")
        data = self._get_valid_recruitment_data(tag_ids=[self.tag1.id, self.tag2.id])
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "공고가 작성되었습니다.")
        self.assertTrue(Recruitment.objects.filter(title=data["title"]).exists())

    def test_create_recruitment_unauthenticated(self) -> None:
        """비인증 사용자 공고 작성 불가"""
        self.client.force_authenticate(user=None)
        url = reverse("recruitment-list-create")
        data = self._get_valid_recruitment_data()
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_recruitment_with_invalid_data(self) -> None:
        """잘못된 데이터로 공고 작성 실패"""
        url = reverse("recruitment-list-create")
        data = {"title": "짧음", "content": ""}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_recruitments_success(self) -> None:
        """공고 목록 조회 성공"""
        self._create_multiple_recruitments(15)
        url = reverse("recruitment-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 15)

    def test_list_recruitments_excludes_closed(self) -> None:
        """마감된 공고는 목록에서 제외"""
        self._create_multiple_recruitments(10, is_closed=False)
        self._create_recruitment(title="마감 공고", is_closed=True)

        url = reverse("recruitment-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 10)

    def test_list_recruitments_pagination(self) -> None:
        """페이지네이션 동작 확인"""
        self._create_multiple_recruitments(15)
        url = reverse("recruitment-list-create")
        response = self.client.get(url, {"page": "1", "size": "10"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data.get("next"))

    def test_list_recruitments_search(self) -> None:
        """검색 기능 동작 확인"""
        self._create_recruitment(title="Django 백엔드 스터디")
        self._create_multiple_recruitments(5, title_prefix="React")

        url = reverse("recruitment-list-create")
        response = self.client.get(url, {"search": "Django"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_list_recruitments_sort_by_latest(self) -> None:
        """최신순 정렬 확인"""
        self._create_recruitment(title="첫번째")
        self._create_recruitment(title="두번째")

        url = reverse("recruitment-list-create")
        response = self.client.get(url, {"sort": "latest"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["title"], "두번째")

    def test_list_recruitments_filter_by_tags(self) -> None:
        """태그 필터링 동작 확인"""
        recruitment1 = self._create_recruitment(title="Python 공고")
        recruitment1.recruitment_tags.create(tag=self.tag1)

        recruitment2 = self._create_recruitment(title="Django 공고")
        recruitment2.recruitment_tags.create(tag=self.tag2)

        self._create_recruitment(title="태그 없는 공고")

        url = reverse("recruitment-list-create")
        response = self.client.get(url, {"tags": "Python"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Python 공고")

    def test_list_recruitments_filter_by_multiple_tags(self) -> None:
        """여러 태그 필터링 동작 확인"""
        recruitment1 = self._create_recruitment(title="Python 공고")
        recruitment1.recruitment_tags.create(tag=self.tag1)

        recruitment2 = self._create_recruitment(title="Django 공고")
        recruitment2.recruitment_tags.create(tag=self.tag2)

        url = reverse("recruitment-list-create")
        response = self.client.get(url, {"tags": "Python,Django"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_list_recruitments_pagination_previous_url(self) -> None:
        """페이지네이션 이전 URL 확인"""
        self._create_multiple_recruitments(25)
        url = reverse("recruitment-list-create")
        response = self.client.get(url, {"page": "2", "size": "10"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data.get("previous"))
        self.assertIn("page=1", response.data["previous"])

    def test_create_recruitment_with_files_and_images(self) -> None:
        """파일과 이미지 첨부된 공고 작성"""
        url = reverse("recruitment-list-create")
        data = self._get_valid_recruitment_data(tag_ids=[self.tag1.id])
        data["files"] = [
            {"file_name": "test.pdf", "file_url": "https://example.com/test.pdf"},
            {"file_name": "document.docx", "file_url": "https://example.com/doc.docx"},
        ]
        data["image_urls"] = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.png",
        ]
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recruitment = Recruitment.objects.get(title=data["title"])
        self.assertEqual(recruitment.attachments.count(), 2)
        self.assertEqual(recruitment.images.count(), 2)


class RecruitmentDetailUpdateDeleteViewTest(RecruitmentViewAPITestCase):
    """공고 상세 조회/수정/삭제 테스트"""

    def setUp(self) -> None:
        super().setUp()
        self.recruitment = self._create_recruitment(title="테스트 공고")

    def test_detail_recruitment_success(self) -> None:
        """공고 상세 조회 성공"""
        url = reverse("recruitment-detail", kwargs={"recruitments_uuid": self.recruitment.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.recruitment.title)

    def test_detail_recruitment_increases_view_count(self) -> None:
        """조회수 증가 확인"""
        initial_views = self.recruitment.views_count
        url = reverse("recruitment-detail", kwargs={"recruitments_uuid": self.recruitment.uuid})
        self.client.get(url)

        self.recruitment.refresh_from_db()
        self.assertEqual(self.recruitment.views_count, initial_views + 1)

    def test_detail_recruitment_not_found(self) -> None:
        """존재하지 않는 공고 조회 404"""
        url = reverse("recruitment-detail", kwargs={"recruitments_uuid": "00000000-0000-0000-0000-000000000000"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_recruitment_success(self) -> None:
        """공고 수정 성공"""
        url = reverse("recruitment-detail", kwargs={"recruitments_uuid": self.recruitment.uuid})
        data = {"title": "수정된 제목"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "수정된 제목")

    def test_update_recruitment_unauthorized(self) -> None:
        """작성자 아닌 사용자 수정 실패"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("recruitment-detail", kwargs={"recruitments_uuid": self.recruitment.uuid})
        data = {"title": "수정 시도"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_closed_recruitment_fails(self) -> None:
        """마감된 공고 수정 실패"""
        self.recruitment.is_closed = True
        self.recruitment.save()

        url = reverse("recruitment-detail", kwargs={"recruitments_uuid": self.recruitment.uuid})
        data = {"title": "수정 시도"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_recruitment_success(self) -> None:
        """공고 삭제 성공"""
        url = reverse("recruitment-detail", kwargs={"recruitments_uuid": self.recruitment.uuid})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recruitment.refresh_from_db()
        self.assertTrue(self.recruitment.is_closed)

    def test_delete_recruitment_unauthorized(self) -> None:
        """작성자 아닌 사용자 삭제 실패"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("recruitment-detail", kwargs={"recruitments_uuid": self.recruitment.uuid})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_already_closed_recruitment_fails(self) -> None:
        """이미 마감된 공고 삭제 실패"""
        self.recruitment.is_closed = True
        self.recruitment.save()

        url = reverse("recruitment-detail", kwargs={"recruitments_uuid": self.recruitment.uuid})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recruitment_with_tags(self) -> None:
        """태그 포함 공고 수정"""
        url = reverse("recruitment-detail", kwargs={"recruitments_uuid": self.recruitment.uuid})
        data = {"tags": [self.tag1.id, self.tag2.id]}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recruitment.refresh_from_db()
        self.assertEqual(self.recruitment.recruitment_tags.count(), 2)

    def test_update_recruitment_with_files(self) -> None:
        """파일 포함 공고 수정"""
        url = reverse("recruitment-detail", kwargs={"recruitments_uuid": self.recruitment.uuid})
        data = {
            "files": [
                {"file_name": "new.pdf", "file_url": "https://example.com/new.pdf"},
            ]
        }
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recruitment.refresh_from_db()
        self.assertEqual(self.recruitment.attachments.count(), 1)
        attachment = self.recruitment.attachments.first()
        assert attachment is not None
        self.assertEqual(attachment.file_name, "new.pdf")

    def test_update_recruitment_with_images(self) -> None:
        """이미지 포함 공고 수정"""
        url = reverse("recruitment-detail", kwargs={"recruitments_uuid": self.recruitment.uuid})
        data = {
            "image_urls": [
                "https://example.com/new1.jpg",
                "https://example.com/new2.jpg",
            ]
        }
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recruitment.refresh_from_db()
        self.assertEqual(self.recruitment.images.count(), 2)

    def test_update_recruitment_replace_tags(self) -> None:
        """기존 태그 교체"""
        self.recruitment.recruitment_tags.create(tag=self.tag1)
        self.assertEqual(self.recruitment.recruitment_tags.count(), 1)

        url = reverse("recruitment-detail", kwargs={"recruitments_uuid": self.recruitment.uuid})
        data = {"tags": [self.tag2.id]}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recruitment.refresh_from_db()
        self.assertEqual(self.recruitment.recruitment_tags.count(), 1)
        recruitment_tag = self.recruitment.recruitment_tags.first()
        assert recruitment_tag is not None
        self.assertEqual(recruitment_tag.tag.id, self.tag2.id)


class RecruitmentMineViewTest(RecruitmentViewAPITestCase):
    """내가 작성한 공고 목록 테스트"""

    def setUp(self) -> None:
        super().setUp()
        self._create_multiple_recruitments(5, title_prefix="내 공고")
        self._create_multiple_recruitments(3, title_prefix="다른 사람 공고", author=self.other_user)

    def test_mine_recruitments_success(self) -> None:
        """내 공고 목록 조회 성공"""
        url = reverse("recruitment-mine")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)

    def test_mine_recruitments_unauthenticated(self) -> None:
        """비인증 사용자 접근 불가"""
        self.client.force_authenticate(user=None)
        url = reverse("recruitment-mine")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_mine_recruitments_filter_by_is_closed(self) -> None:
        """마감 여부 필터링"""
        recruitment = Recruitment.objects.filter(author=self.user).first()
        if recruitment:
            recruitment.is_closed = True
            recruitment.save()

        url = reverse("recruitment-mine")
        response = self.client.get(url, {"is_closed": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_mine_recruitments_search(self) -> None:
        """검색 기능 동작 확인"""
        self._create_recruitment(title="특별한 공고")

        url = reverse("recruitment-mine")
        response = self.client.get(url, {"search": "특별한"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)
