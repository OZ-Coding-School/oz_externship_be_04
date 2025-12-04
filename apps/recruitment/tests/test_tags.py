from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.recruitment.models import Tag

User = get_user_model()


class TestTags(APITestCase):

    def setUp(self) -> None:

        # 로그인 유저 생성
        self.user = User.objects.create(
            email="test@example.com",
            name="test",
            nickname="test1",
            phone_number="01012345678",
            gender="F",
            birthday="2000-01-01",
            profile_img_url="http://example.com",
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)

        # 태그 생성
        self.tag1 = Tag.objects.create(name="Python")
        self.tag2 = Tag.objects.create(name="Django")
        self.tag3 = Tag.objects.create(name="database")
        self.tag4 = Tag.objects.create(name="javascript")
        self.tag5 = Tag.objects.create(name="aws")
        self.tag6 = Tag.objects.create(name="파이썬")

        self.tag_list_url = reverse("tag-list")

    def test_tag_search_partial_match(self) -> None:
        response = self.client.get(self.tag_list_url, {"keyword": "Py"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["name"], "Python")

    def test_tag_search_exact_match(self) -> None:
        response = self.client.get(self.tag_list_url, {"keyword": "Django"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["name"], "Django")

    def test_get_tags_fail(self) -> None:
        response = self.client.get(self.tag_list_url, {"keyword": "Framework"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])

    def test_tag_creation_success(self) -> None:
        response = self.client.post(self.tag_list_url, {"name": "FastAPI"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Tag.objects.filter(name="FastAPI").exists())

    def test_tag_creation_conflict(self) -> None:
        response = self.client.post(self.tag_list_url, {"name": "Python"})
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_tag_creation_empty_name(self) -> None:
        response = self.client.post(self.tag_list_url, {"name": ""})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error_detail"], "name은 필수입니다.")

    def test_tag_creation_unauthenticated(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.client.post(self.tag_list_url, {"name": "NewTag"})
        self.assertEqual(response.status_code, 401)

    def test_tag_pagination(self) -> None:
        response = self.client.get(self.tag_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertEqual(response.data["count"], 6)
