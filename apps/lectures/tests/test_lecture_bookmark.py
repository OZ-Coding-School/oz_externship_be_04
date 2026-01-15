from typing import cast

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response as DRFResponse
from rest_framework.test import APIClient

from apps.lectures.models import CrawledLecture, LectureBookmark

User = get_user_model()


class LectureBookmarkViewTest(TestCase):
    def destroy_url(self, lecture_id: int) -> str:
        return reverse(
            "lecture_bookmarks:lecture-bookmark-destroy",
            kwargs={"lecture_id": lecture_id},
        )

    def setUp(self) -> None:
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="user@example.com",
            password="testpassword123",
            nickname="user",
            phone_number="01012345678",
            gender="M",
        )
        self.client.force_authenticate(self.user)

        self.lecture = CrawledLecture.objects.create(
            external_id=1,
            title="테스트 강의",
            instructor="테스트 강사",
            description="테스트 설명",
            total_class_time=90,
            original_price=10000,
            discount_price=8000,
            difficulty="HARD",
            thumbnail_img_url="https://thumbnail.com",
            average_rating=4.5,
            platform="UDEMY",
            url_link="https://url.com",
        )

        self.list_url = reverse("lecture_bookmarks:lecture-bookmark-list-create")

    @override_settings(DEBUG=False)
    def test_list_bookmarks_returns_only_current_user_bookmarks(self) -> None:
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpassword123",
            nickname="other",
            phone_number="01087654321",
            gender="M",
        )

        another_lecture = CrawledLecture.objects.create(
            external_id=2,
            title="다른 강의",
            instructor="다른 강사",
            description="다른 설명",
            total_class_time=120,
            original_price=20000,
            discount_price=15000,
            difficulty="HARD",
            thumbnail_img_url="https://thumbnail2.com",
            average_rating=4.2,
            platform="UDEMY",
            url_link="https://url2.com",
        )

        LectureBookmark.objects.create(user=self.user, lecture=self.lecture)
        LectureBookmark.objects.create(user=self.user, lecture=another_lecture)
        LectureBookmark.objects.create(user=other_user, lecture=self.lecture)

        response = cast(DRFResponse, self.client.get(self.list_url))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

        titles = {item["title"] for item in response.data["results"]}
        self.assertEqual(titles, {"테스트 강의", "다른 강의"})

    @override_settings(DEBUG=False)
    def test_list_bookmarks_can_filter_by_search(self) -> None:
        LectureBookmark.objects.create(user=self.user, lecture=self.lecture)

        python_lecture = CrawledLecture.objects.create(
            external_id=3,
            title="파이썬 입문",
            instructor="김파이썬",
            description="파이썬 설명",
            total_class_time=100,
            original_price=5000,
            discount_price=4000,
            difficulty="HARD",
            thumbnail_img_url="https://py.com",
            average_rating=4.3,
            platform="UDEMY",
            url_link="https://py.com/lecture",
        )
        LectureBookmark.objects.create(user=self.user, lecture=python_lecture)

        response = cast(
            DRFResponse,
            self.client.get(self.list_url, {"search": "파이썬"}),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = {item["title"] for item in response.data["results"]}
        self.assertEqual(titles, {"파이썬 입문"})

    @override_settings(DEBUG=False)
    def test_post_creates_bookmark_when_not_exists(self) -> None:
        payload = {"lecture": self.lecture.id}

        response = cast(
            DRFResponse,
            self.client.post(self.list_url, data=payload, format="json"),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("detail", response.data)
        self.assertTrue(LectureBookmark.objects.filter(user=self.user, lecture=self.lecture).exists())

    @override_settings(DEBUG=False)
    def test_post_toggles_bookmark_when_already_exists(self) -> None:
        LectureBookmark.objects.create(user=self.user, lecture=self.lecture)

        payload = {"lecture": self.lecture.id}
        response = cast(
            DRFResponse,
            self.client.post(self.list_url, data=payload, format="json"),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertFalse(LectureBookmark.objects.filter(user=self.user, lecture=self.lecture).exists())

    @override_settings(DEBUG=False)
    def test_delete_removes_bookmark(self) -> None:
        LectureBookmark.objects.create(user=self.user, lecture=self.lecture)

        url = self.destroy_url(self.lecture.id)
        response = cast(DRFResponse, self.client.delete(url))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertFalse(LectureBookmark.objects.filter(user=self.user, lecture=self.lecture).exists())

    @override_settings(DEBUG=False)
    def test_delete_returns_404_when_bookmark_not_found(self) -> None:
        url = self.destroy_url(self.lecture.id)
        response = cast(DRFResponse, self.client.delete(url))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error_detail", response.data)

    @override_settings(DEBUG=False)
    def test_unauthenticated_requests_are_rejected(self) -> None:
        client = APIClient()

        res_get = client.get(self.list_url)
        self.assertEqual(res_get.status_code, status.HTTP_401_UNAUTHORIZED)

        res_post = client.post(self.list_url, data={"lecture": self.lecture.id}, format="json")
        self.assertEqual(res_post.status_code, status.HTTP_401_UNAUTHORIZED)

        url = self.destroy_url(self.lecture.id)
        res_delete = client.delete(url)
        self.assertEqual(res_delete.status_code, status.HTTP_401_UNAUTHORIZED)
