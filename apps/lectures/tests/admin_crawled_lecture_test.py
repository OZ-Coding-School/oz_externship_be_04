from typing import cast

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response as DRFResponse
from rest_framework.test import APIClient

from apps.lectures.models import CrawledLecture

User = get_user_model()


class AdminCrawledLectureViewTest(TestCase):
    def setUp(self) -> None:
        self.admin = User.objects.create_superuser(
            email="admin@admin.com",
            password="ozcoding",
            nickname="admin",
            phone_number="01012345678",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

        for i in range(1, 16):
            CrawledLecture.objects.create(
                external_id=i,
                title=f"제목 {i}",
                instructor=f"강사 {i}",
                description="테스트 설명",
                total_class_time=i * 10,
                original_price=10000 + i,
                discount_price=8000 + i,
                difficulty="HARD",
                thumbnail_img_url=f"https://thumbnail{i}.com",
                average_rating=4.5,
                platform="UDEMY",
                url_link=f"https://url{i}.com",
            )

        self.url = reverse("admin_crawled_lectures")

    # 기본적인 조회
    def test_admin_can_get_lecture_list(self) -> None:
        response = cast(DRFResponse, self.client.get(self.url))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)

    # 페이지네이션 잘 가는지
    def test_pagination_page_2(self) -> None:
        response = cast(DRFResponse, self.client.get(self.url, {"page": 2}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)

    # 제목으로 검색
    def test_search_by_title(self) -> None:
        response = cast(DRFResponse, self.client.get(self.url, {"search": "제목 3"}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "제목 3")

    # 강사명으로 검색
    def test_search_by_instructor(self) -> None:
        response = cast(DRFResponse, self.client.get(self.url, {"search": "강사 5"}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["instructor"], "강사 5")

    # 로그인 안했을 때
    def test_unauthenticated_user_cannot_access(self) -> None:
        client = APIClient()
        res = client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # 일반유저로 했을 때
    def test_non_admin_user_forbidden(self) -> None:
        user = User.objects.create_user(email="user@example.com", password="userpass")
        client = APIClient()
        client.force_authenticate(user)

        res = client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
