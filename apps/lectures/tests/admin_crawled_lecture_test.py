from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from django.contrib.auth import get_user_model
from apps.lectures.models import CrawledLecture

User = get_user_model()


class AdminCrawledLectureViewTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@admin.com",
            password="ozcoding"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

        for i in range(1, 16):
            CrawledLecture.objects.create(
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

        self.url = reverse("v1_admin_crawled_lectures_list")

    def test_admin_can_get_lecture_list(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)  # 페이지당 10개

    def test_pagination_page_2(self):
        response = self.client.get(self.url, {"page": 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)  # 16개 중 나머지 6번째~15번째

    def test_search_by_title(self):
        response = self.client.get(self.url, {"search": "제목 3"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "제목 3")

    def test_search_by_instructor(self):
        response = self.client.get(self.url, {"search": "강사 5"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["instructor"], "강사 5")

    def test_unauthenticated_user_cannot_access(self):
        client = APIClient()
        res = client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_user_forbidden(self):
        user = User.objects.create_user(email="user@example.com", password="userpass")
        client = APIClient()
        client.force_authenticate(user)

        res = client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
