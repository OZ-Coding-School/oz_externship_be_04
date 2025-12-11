from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.lectures.models import (
    Category,
    CrawledLecture,
    CrawledLectureReview,
    LectureCategory,
)

User = get_user_model()


class CrawledLectureViewTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.lectures = []

        for i in range(1, 16):
            lecture = CrawledLecture.objects.create(
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
            self.lectures.append(lecture)

            for j in range(1, 3):
                category, _ = Category.objects.get_or_create(name=f"카테고리 {j}")
                LectureCategory.objects.create(lecture=lecture, category=category)

            for k in range(1, 4):
                CrawledLectureReview.objects.create(
                    lecture=lecture, external_id=k, rating=4.0 + k * 0.1, content=f"테스트 리뷰 {k}"
                )

        self.url = reverse("lectures")

    def test_list_default_pagination_and_nested_fields(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 12)
        self.assertEqual(data["count"], 15)

        first = data["results"][0]
        self.assertIn("categories", first)
        self.assertEqual(len(first["categories"]), 2)
        self.assertIn("reviews", first)
        self.assertEqual(len(first["reviews"]), 3)

        self.assertIn("카테고리 1", [c["name"] for c in first["categories"]])
        self.assertIn("테스트 리뷰 1", [r["content"] for r in first["reviews"]])

    def test_list_custom_page_size(self) -> None:
        response = self.client.get(self.url, {"page_size": 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data["results"]), 5)
        self.assertEqual(data["count"], 15)

    def test_list_search_title(self) -> None:
        response = self.client.get(self.url, {"search": "제목 1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(all("제목 1" in item["title"] for item in data["results"]))

    def test_list_search_instructor(self) -> None:
        response = self.client.get(self.url, {"search": "강사 2"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue(all("강사 2" in item["instructor"] for item in data["results"]))

    def test_list_sort_high_price(self) -> None:
        response = self.client.get(self.url, {"sort": "high_price"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        prices = [item["discounted_price"] for item in data["results"]]
        self.assertEqual(prices, sorted(prices, reverse=True)[: len(prices)])

    def test_anonymous_access(self) -> None:
        client = APIClient()
        response = client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
