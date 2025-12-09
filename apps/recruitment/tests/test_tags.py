from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.recruitment.models import Tag
from apps.recruitment.serializers.tags import (
    RecruitmentTagUpdateSerializer,
    TagSerializer,
)

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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("blank", str(response.data["name"][0]))

    def test_tag_creation_unauthenticated(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.client.post(self.tag_list_url, {"name": "Framework"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tag_pagination(self) -> None:
        response = self.client.get(self.tag_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertEqual(response.data["count"], 6)

    def test_tag_creation_fail_too_long(self) -> None:
        invalid_data = {"name": "안녕하세요 태그 길이 20자 이상 테스트 검증용 입니다."}
        serializer = TagSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)
        self.assertIn("글자 수가 20 이하", str(serializer.errors["name"]))

    def test_tag_name_invalid_characters(self) -> None:
        """허용되지 않는 문자가 포함된 태그 이름은 실패"""
        invalid_names = [
            "Python!",  # 느낌표
            "Django@",  # @ 기호
            "테스트#",  # # 기호
            "😊",  # 이모지
        ]

        for name in invalid_names:
            serializer = TagSerializer(data={"name": name})
            self.assertFalse(serializer.is_valid())
            self.assertIn("허용되지 않는", str(serializer.errors["name"]))

    def test_tag_name_valid_characters(self) -> None:
        """하이픈, 공백, 숫자, 자음일경우 허용되는지 테스트"""
        valid_names = [
            "ㄱㄱㄱㄱㄱㄷ",  # 자음
            "12345",  # 숫자
            "테-스트",  # # 하이픈
            "dja ngo",  # 공백
            "Python_3",  # 영문, 숫자, 언더바
            "태극기",  # 한글 테스트
        ]

        for name in valid_names:
            serializer = TagSerializer(data={"name": name})
            self.assertTrue(serializer.is_valid(), f"유효한 이름 '{name}'이 is_valid()에서 실패: {serializer.errors}")
            tag = serializer.save()
            self.assertTrue(Tag.objects.filter(name=name).exists(), f"'{name}' 저장 실패 — DB에서 검색되지 않음")

    def test_validate_tags_too_many(self) -> None:
        """태그 6개 이상 입력 시 실패"""
        data = {
            "tags": [
                self.tag1.id,
                self.tag2.id,
                self.tag3.id,
                self.tag4.id,
                self.tag5.id,
                self.tag6.id,
            ]
        }
        serializer = RecruitmentTagUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("5개이상", str(serializer.errors["tags"]))

    def test_validate_tags_duplicates(self) -> None:
        """중복된 태그 ID 입력 시 실패"""
        data = {"tags": [self.tag1.id, self.tag2.id, self.tag2.id, self.tag3.id]}
        serializer = RecruitmentTagUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("중복될 수 없습니다", str(serializer.errors["tags"]))
