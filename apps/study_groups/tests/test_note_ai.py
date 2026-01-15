from datetime import datetime, timedelta
from typing import Any
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.study_groups.models import StudyGroup, StudyNote
from apps.study_groups.services.note_ai import StudyNoteAIService
from apps.users.models import User


class StudyNoteAIServiceE2ETest(TestCase):
    """StudyNote AI 요약 E2E 테스트"""

    def setUp(self) -> None:
        """테스트 환경 설정"""
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="test@example.com",
            name="테스트",
            nickname="테스트유저",
            phone_number="010-1234-5678",
            gender="M",
            password="testpass123!",
            is_active=True,
        )

        now = timezone.now()
        self.study_group = StudyGroup.objects.create(
            name="파이썬스터디",
            introduction="파이썬 기초 학습",
            max_headcount=10,
            start_at=now,
            end_at=now + timedelta(days=30),
            status=StudyGroup.StudyGroupStatusChoices.ONGOING,
        )

        self.mock_ai_response = """### 2025년 12월 22일 Sunday 테스트유저님의 학습 기록 요약입니다.

## 학습 내용 요약
파이썬의 기본 문법과 변수 선언 방법을 학습했습니다. 데이터 타입과 조건문, 반복문의 기초를 익혔으며, 함수 정의와 호출 방법을 실습했습니다.

## 학습한 키워드
파이썬 기본 문법
변수와 데이터 타입
조건문(if/else)
반복문(for/while)
함수 정의

## 추가로 학습하면 좋을 내용 추천
- 파이썬 클래스와 객체지향 프로그래밍 개념
- 리스트, 딕셔너리 등 파이썬 자료구조 심화
- 예외 처리(try/except)와 디버깅 기법"""

    @patch("apps.study_groups.services.note_ai.StudyNoteAIService._CLIENT")
    def test_create_note_with_ai_summary(self, mock_client: Mock) -> None:
        """노트 작성 시 AI 요약이 자동으로 생성되는지 테스트"""
        mock_response = Mock()
        mock_response.text = self.mock_ai_response
        mock_client.models.generate_content.return_value = mock_response

        self.client.force_authenticate(user=self.user)  # type: ignore[attr-defined]

        note_data = {
            "title": "파이썬 1일차 학습 요약",
            "content": "오늘은 파이썬의 기본 문법을 배웠습니다. 변수 선언, 조건문, 반복문, 함수 정의 등을 학습했습니다.",
        }

        response = self.client.post(
            f"/api/v1/study-groups/{self.study_group.id}/notes",
            note_data,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["detail"], "스터디 학습 기록 작성에 성공했습니다.")  # type: ignore[attr-defined]

        note = StudyNote.objects.get(
            study_group=self.study_group,
            author=self.user,
            title=note_data["title"],
        )

        self.assertIsNotNone(note.ai_summary)
        assert note.ai_summary is not None  # Type narrowing
        self.assertIn("학습 내용 요약", note.ai_summary)
        self.assertIn("학습한 키워드", note.ai_summary)
        self.assertIn("추가로 학습하면 좋을 내용 추천", note.ai_summary)

    @patch("apps.study_groups.services.note_ai.StudyNoteAIService._CLIENT")
    def test_get_note_detail_includes_ai_summary(self, mock_client: Mock) -> None:
        """노트 상세 조회 시 AI 요약이 포함되는지 테스트"""
        mock_response = Mock()
        mock_response.text = self.mock_ai_response
        mock_client.models.generate_content.return_value = mock_response

        self.client.force_authenticate(user=self.user)  # type: ignore[attr-defined]

        note_data = {
            "title": "파이썬 2일차 학습 요약",
            "content": "리스트와 딕셔너리를 사용하는 방법을 배웠습니다. 리스트 컴프리헨션도 실습했습니다.",
        }

        create_response = self.client.post(
            f"/api/v1/study-groups/{self.study_group.id}/notes",
            note_data,
            format="json",
        )

        self.assertEqual(create_response.status_code, 200)

        note = StudyNote.objects.get(
            study_group=self.study_group,
            author=self.user,
            title=note_data["title"],
        )

        detail_response = self.client.get(f"/api/v1/study-groups/{self.study_group.id}/notes/{note.id}")

        self.assertEqual(detail_response.status_code, 200)
        response_data: Any = detail_response.data  # type: ignore[attr-defined]
        self.assertIn("ai_summary", response_data)
        self.assertIsNotNone(response_data["ai_summary"])
        self.assertIn("학습 내용 요약", response_data["ai_summary"])

    @patch("apps.study_groups.services.note_ai.StudyNoteAIService._CLIENT")
    def test_short_content_skips_ai_summary(self, mock_client: Mock) -> None:
        """내용이 너무 짧으면 AI 요약을 건너뛰는지 테스트"""
        self.client.force_authenticate(user=self.user)  # type: ignore[attr-defined]

        note_data = {
            "title": "짧은 노트",
            "content": "짧음",
        }

        response = self.client.post(
            f"/api/v1/study-groups/{self.study_group.id}/notes",
            note_data,
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        note = StudyNote.objects.get(
            study_group=self.study_group,
            author=self.user,
            title=note_data["title"],
        )

        self.assertIsNotNone(note.ai_summary)
        assert note.ai_summary is not None  # Type narrowing
        self.assertIn("자동요약이 생략되었습니다", note.ai_summary)

        mock_client.models.generate_content.assert_not_called()

    @patch("apps.study_groups.services.note_ai.StudyNoteAIService._CLIENT")
    def test_ai_api_failure_retry_logic(self, mock_client: Mock) -> None:
        """AI API 실패 시 재시도 로직 테스트"""
        mock_client.models.generate_content.side_effect = [
            Exception("API Error 1"),
            Exception("API Error 2"),
            Mock(text=self.mock_ai_response),
        ]

        note = StudyNote.objects.create(
            study_group=self.study_group,
            author=self.user,
            title="재시도 테스트",
            content="이것은 재시도 로직을 테스트하기 위한 충분히 긴 내용입니다. 파이썬은 정말 재미있는 언어입니다.",
        )

        ai_summary = StudyNoteAIService.summarize(note, max_retries=3)

        self.assertIn("학습 내용 요약", ai_summary)

        self.assertEqual(mock_client.models.generate_content.call_count, 3)

    @patch("apps.study_groups.services.note_ai.StudyNoteAIService._CLIENT")
    def test_ai_api_all_retries_failed(self, mock_client: Mock) -> None:
        """AI API 모든 재시도 실패 시 에러 메시지 저장 테스트"""
        mock_client.models.generate_content.side_effect = Exception("API Error")

        note = StudyNote.objects.create(
            study_group=self.study_group,
            author=self.user,
            title="실패 테스트",
            content="이것은 AI API 실패를 테스트하기 위한 충분히 긴 내용입니다. 테스트 데이터입니다.",
        )

        ai_summary = StudyNoteAIService.summarize(note, max_retries=3)

        self.assertIn("AI요약 오류", ai_summary)

        self.assertEqual(mock_client.models.generate_content.call_count, 3)

    @patch("apps.study_groups.services.note_ai.StudyNoteAIService._CLIENT")
    def test_ai_summary_with_files_and_images(self, mock_client: Mock) -> None:
        """파일과 이미지가 포함된 노트의 AI 요약 테스트"""
        mock_response = Mock()
        mock_response.text = self.mock_ai_response
        mock_client.models.generate_content.return_value = mock_response

        self.client.force_authenticate(user=self.user)  # type: ignore[attr-defined]

        note_data = {
            "title": "Django REST Framework 학습",
            "content": "Django REST Framework의 Serializer와 ViewSet을 학습했습니다. API 개발의 기초를 다졌습니다.",
            "images": ["https://example.com/image1.png", "https://example.com/image2.png"],
            "files": [
                {"file_name": "drf_notes.pdf", "file_url": "https://example.com/drf_notes.pdf"},
                {"file_name": "code_samples.py", "file_url": "https://example.com/code_samples.py"},
            ],
        }

        response = self.client.post(
            f"/api/v1/study-groups/{self.study_group.id}/notes",
            note_data,
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        note = StudyNote.objects.get(
            study_group=self.study_group,
            author=self.user,
            title=note_data["title"],
        )

        self.assertIsNotNone(note.ai_summary)
        assert note.ai_summary is not None  # Type narrowing
        self.assertIn("학습 내용 요약", note.ai_summary)

        self.assertEqual(note.images.count(), 2)
        self.assertEqual(note.attachments.count(), 2)

    def test_ai_service_validate_summary(self) -> None:
        """AI 요약 검증 로직 테스트"""
        valid_summary = """
        ### 2025년 1월 1일 월요일 테스트님의 학습 기록 요약입니다.

        ## 학습 내용 요약
        파이썬의 기본 문법을 학습했습니다.

        ## 학습한 키워드
        파이썬, 변수, 함수

        ## 추가로 학습하면 좋을 내용 추천
        객체지향 프로그래밍을 학습하면 좋습니다.
        """
        self.assertTrue(StudyNoteAIService._validate_summary(valid_summary))

        short_summary = "짧은 요약"
        self.assertFalse(StudyNoteAIService._validate_summary(short_summary))

        empty_summary = ""
        self.assertFalse(StudyNoteAIService._validate_summary(empty_summary))

        error_summary = "요약 오류가 발생했습니다"
        self.assertFalse(StudyNoteAIService._validate_summary(error_summary))

        missing_section_summary = (
            "이것은 충분히 긴 요약이지만 필수 섹션이 없습니다. 열 개 이상의 단어가 포함되어 있습니다."
        )
        self.assertFalse(StudyNoteAIService._validate_summary(missing_section_summary))
