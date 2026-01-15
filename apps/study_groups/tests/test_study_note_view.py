from typing import Any
from unittest.mock import Mock, patch

from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.study_groups.serializers.study_note import (
    StudyNoteCreateSerializer,
    StudyNoteUpdateSerializer,
)
from apps.study_groups.views.study_note import (
    StudyNoteDetailView,
    StudyNoteListCreateView,
)


class StudyNoteCreateSerializerTest(TestCase):
    """StudyNoteCreateSerializer 유닛 테스트"""

    def test_valid_data(self) -> None:
        """정상 데이터 검증"""
        data = {
            "title": "Test Title",
            "content": "Test Content",
            "images": ["https://example.com/image.png"],
            "files": [{"file_name": "test.pdf", "file_url": "https://example.com/test.pdf"}],
        }
        serializer = StudyNoteCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_missing_title(self) -> None:
        """title 누락"""
        data = {"content": "Content"}
        serializer = StudyNoteCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)

    def test_missing_content(self) -> None:
        """content 누락"""
        data = {"title": "Title"}
        serializer = StudyNoteCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("content", serializer.errors)

    def test_empty_content(self) -> None:
        """빈 content"""
        serializer = StudyNoteCreateSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_content("")

    def test_whitespace_content(self) -> None:
        """공백만 있는 content"""
        serializer = StudyNoteCreateSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_content("   ")

    def test_files_missing_file_name(self) -> None:
        """file_name 누락"""
        serializer = StudyNoteCreateSerializer()
        files = [{"file_url": "https://example.com/test.pdf"}]
        with self.assertRaises(ValidationError):
            serializer.validate_files(files)

    def test_files_missing_file_url(self) -> None:
        """file_url 누락"""
        serializer = StudyNoteCreateSerializer()
        files = [{"file_name": "test.pdf"}]
        with self.assertRaises(ValidationError):
            serializer.validate_files(files)

    def test_optional_fields_default(self) -> None:
        """선택적 필드 기본값"""
        data = {"title": "Title", "content": "Content"}
        serializer = StudyNoteCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["images"], [])
        self.assertEqual(serializer.validated_data["files"], [])


class StudyNoteUpdateSerializerTest(TestCase):
    """StudyNoteUpdateSerializer 유닛 테스트"""

    def test_partial_update_title_only(self) -> None:
        """부분 업데이트 - title만"""
        data = {"title": "New Title"}
        serializer = StudyNoteUpdateSerializer(data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        self.assertIn("title", serializer.validated_data)
        self.assertNotIn("content", serializer.validated_data)

    def test_partial_update_content_only(self) -> None:
        """부분 업데이트 - content만"""
        data = {"content": "New Content"}
        serializer = StudyNoteUpdateSerializer(data=data, partial=True)
        self.assertTrue(serializer.is_valid())

    def test_empty_content_validation(self) -> None:
        """빈 content 검증"""
        serializer = StudyNoteUpdateSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_content("   ")


class StudyNoteListCreateViewTest(TestCase):
    """StudyNoteListCreateView 유닛 테스트"""

    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.view = StudyNoteListCreateView.as_view()
        self.user = Mock()
        self.user.id = 1
        self.user.is_authenticated = True

    @patch("apps.study_groups.views.study_note.get_object_or_404")
    @patch("apps.study_groups.views.study_note.StudyNote.objects.filter")
    def test_get_list(self, mock_filter: Mock, mock_get_object: Mock) -> None:
        """GET - 목록 조회"""
        mock_group = Mock()
        mock_get_object.return_value = mock_group

        mock_queryset = Mock()
        mock_queryset.select_related.return_value.order_by.return_value = []
        mock_filter.return_value = mock_queryset

        request = self.factory.get("/study-groups/1/notes/")
        force_authenticate(request, user=self.user)

        response = self.view(request, group_id=1)

        self.assertEqual(response.status_code, 200)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)

    @patch("apps.study_groups.views.study_note.StudyNoteAIService.summarize")
    @patch("apps.study_groups.views.study_note.get_object_or_404")
    @patch("apps.study_groups.views.study_note.StudyNote.objects.create")
    @patch("apps.study_groups.views.study_note.StudyNoteCreateSerializer")
    def test_post_create(
        self,
        mock_serializer_class: Mock,
        mock_create: Mock,
        mock_get_object: Mock,
        mock_ai_summarize: Mock,
    ) -> None:
        """POST - 생성"""
        mock_group = Mock()
        mock_get_object.return_value = mock_group

        mock_serializer = Mock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {
            "title": "Test",
            "content": "Content",
            "images": [],
            "files": [],
        }
        mock_serializer_class.return_value = mock_serializer

        mock_note = Mock()
        mock_create.return_value = mock_note

        # AI 요약 mock
        mock_ai_summarize.return_value = "AI 요약 결과"

        request = self.factory.post(
            "/study-groups/1/notes/",
            {"title": "Test", "content": "Content"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = self.view(request, group_id=1)

        self.assertEqual(response.status_code, 200)
        mock_create.assert_called_once()
        mock_ai_summarize.assert_called_once_with(mock_note)


class StudyNoteDetailViewTest(TestCase):
    """StudyNoteDetailView 유닛 테스트"""

    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.view = StudyNoteDetailView.as_view()
        self.user = Mock()
        self.user.id = 1
        self.user.is_authenticated = True

    @patch("apps.study_groups.views.study_note.get_object_or_404")
    @patch("apps.study_groups.views.study_note.StudyNoteDetailSerializer")
    def test_get_detail(self, mock_serializer_class: Mock, mock_get_object: Mock) -> None:
        """GET - 상세 조회"""
        mock_note = Mock()
        mock_note.id = 1
        mock_get_object.return_value = mock_note

        mock_serializer = Mock()
        mock_serializer.data = {"id": 1, "title": "Test"}
        mock_serializer_class.return_value = mock_serializer

        request = self.factory.get("/study-groups/1/notes/1/")
        force_authenticate(request, user=self.user)

        response = self.view(request, group_id=1, note_id=1)

        self.assertEqual(response.status_code, 200)

    @patch("apps.study_groups.views.study_note.get_object_or_404")
    @patch("apps.study_groups.views.study_note.StudyNoteUpdateSerializer")
    @patch("apps.study_groups.views.study_note.StudyNoteUpdateResponseSerializer")
    def test_patch_update(
        self,
        mock_response_serializer: Mock,
        mock_update_serializer: Mock,
        mock_get_object: Mock,
    ) -> None:
        """PATCH - 수정"""
        mock_note = Mock()
        mock_note.author = self.user
        mock_note.save = Mock()
        mock_get_object.return_value = mock_note

        mock_serializer = Mock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {"title": "New Title"}
        mock_update_serializer.return_value = mock_serializer

        mock_response = Mock()
        mock_response.data = {"id": 1}
        mock_response_serializer.return_value = mock_response

        request = self.factory.patch(
            "/study-groups/1/notes/1/",
            {"title": "New Title"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = self.view(request, group_id=1, note_id=1)

        self.assertEqual(response.status_code, 200)
        mock_note.save.assert_called_once()

    @patch("apps.study_groups.views.study_note.get_object_or_404")
    def test_patch_permission_denied(self, mock_get_object: Mock) -> None:
        """PATCH - 권한 없음"""
        other_user = Mock()
        other_user.id = 2

        mock_note = Mock()
        mock_note.author = other_user
        mock_get_object.return_value = mock_note

        request = self.factory.patch(
            "/study-groups/1/notes/1/",
            {"title": "Hack"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = self.view(request, group_id=1, note_id=1)

        self.assertEqual(response.status_code, 403)

    @patch("apps.study_groups.views.study_note.get_object_or_404")
    def test_delete(self, mock_get_object: Mock) -> None:
        """DELETE - 삭제"""
        mock_note = Mock()
        mock_note.author = self.user
        mock_note.delete = Mock()
        mock_get_object.return_value = mock_note

        request = self.factory.delete("/study-groups/1/notes/1/")
        force_authenticate(request, user=self.user)

        response = self.view(request, group_id=1, note_id=1)

        self.assertEqual(response.status_code, 200)
        mock_note.delete.assert_called_once()

    @patch("apps.study_groups.views.study_note.get_object_or_404")
    def test_delete_permission_denied(self, mock_get_object: Mock) -> None:
        """DELETE - 권한 없음"""
        other_user = Mock()
        other_user.id = 2

        mock_note = Mock()
        mock_note.author = other_user
        mock_get_object.return_value = mock_note

        request = self.factory.delete("/study-groups/1/notes/1/")
        force_authenticate(request, user=self.user)

        response = self.view(request, group_id=1, note_id=1)

        self.assertEqual(response.status_code, 403)
