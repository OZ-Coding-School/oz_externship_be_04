from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.application.models import Application, ApplicationStatus
from apps.recruitment.models import Recruitment
from apps.study_groups.models import StudyGroup
from apps.users.models import User


class RecruiterApplicationAPITestCase(APITestCase):
    """작성자용 지원자 관리 API 통합 테스트"""

    def setUp(self) -> None:
        """테스트 기본 데이터 생성"""

        self.author = User.objects.create(
            email="author@test.com",
            nickname="author",
            name="작성자",
            phone_number="01011112222",
            birthday="1990-01-01",
            gender="M",
        )
        self.author.set_password("testpassword1")
        self.author.save()

        self.other_author = User.objects.create(
            email="other@test.com",
            nickname="other",
            name="다른작성자",
            phone_number="01022223333",
            birthday="1990-01-01",
            gender="F",
        )
        self.other_author.set_password("testpassword1")
        self.other_author.save()

        self.applicant = User.objects.create(
            email="applicant@test.com",
            nickname="applicant",
            name="지원자",
            phone_number="01033334444",
            birthday="1990-01-01",
            gender="F",
        )
        self.applicant.set_password("testpassword1")
        self.applicant.save()

        self.study_group = StudyGroup.objects.create(
            name="테스트 스터디",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now(),
        )

        self.recruitment = Recruitment.objects.create(
            author=self.author,
            study_group=self.study_group,
            title="테스트 공고",
            content="테스트 내용",
            estimated_fee=10000,
            expected_headcount=5,
            close_at=timezone.now(),
        )

        self.other_recruitment = Recruitment.objects.create(
            author=self.other_author,
            study_group=self.study_group,
            title="다른 공고",
            content="다른 내용",
            estimated_fee=20000,
            expected_headcount=3,
            close_at=timezone.now(),
        )

        self.application = Application.objects.create(
            recruitment=self.recruitment,
            applicant=self.applicant,
            self_introduction="자기소개",
            motivation="지원 동기",
            objective="목표",
            available_time="10:00 ~ 11:00",
            has_study_experience=True,
            study_experience="경험 있음",
            status=ApplicationStatus.PENDING,
        )

        self.other_application = Application.objects.create(
            recruitment=self.other_recruitment,
            applicant=self.applicant,
            self_introduction="자기소개2",
            motivation="지원 동기2",
            objective="목표2",
            available_time="14:00 ~ 15:00",
            has_study_experience=False,
            study_experience="",
            status=ApplicationStatus.PENDING,
        )

        self.client.force_authenticate(user=self.author)

    def test_application_list_success(self) -> None:
        """[REQ-APLY-002] 작성자용 지원자 목록 조회 성공 (200 OK)"""
        url = reverse("recruiter-application-list", kwargs={"recruitment_uuid": self.recruitment.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.application.id)

    def test_application_list_unauthorized(self) -> None:
        """목록 조회 - 인증 없음 (401 UNAUTHORIZED)"""
        self.client.force_authenticate(user=None)
        url = reverse("recruiter-application-list", kwargs={"recruitment_uuid": self.recruitment.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_application_list_permission_denied(self) -> None:
        """목록 조회 - 권한 없음 (403 FORBIDDEN)"""
        self.client.force_authenticate(user=self.other_author)
        url = reverse("recruiter-application-list", kwargs={"recruitment_uuid": self.recruitment.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)

    def test_application_list_recruitment_not_found(self) -> None:
        """목록 조회 - 공고 없음 (404 NOT FOUND)"""
        url = reverse("recruiter-application-list", kwargs={"recruitment_uuid": "00000000-0000-0000-0000-000000000000"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error_detail", response.data)

    def test_application_review_success(self) -> None:
        """[REQ-APLY-003] 작성자용 지원자 상세 조회 성공 (200 OK)"""
        url = reverse("recruiter-application-review", kwargs={"application_id": self.application.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.application.id)
        self.assertEqual(response.data["self_introduction"], "자기소개")
        self.assertEqual(response.data["motivation"], "지원 동기")

    def test_application_review_unauthorized(self) -> None:
        """상세 조회 - 인증 없음 (401 UNAUTHORIZED)"""
        self.client.force_authenticate(user=None)
        url = reverse("recruiter-application-review", kwargs={"application_id": self.application.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_application_review_permission_denied(self) -> None:
        """상세 조회 - 권한 없음 (403 FORBIDDEN)"""
        self.client.force_authenticate(user=self.other_author)
        url = reverse("recruiter-application-review", kwargs={"application_id": self.application.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)

    def test_application_review_not_found(self) -> None:
        """상세 조회 - 지원 내역 없음 (404 NOT FOUND)"""
        url = reverse("recruiter-application-review", kwargs={"application_id": 99999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error_detail", response.data)

    def test_application_accept_success(self) -> None:
        """[REQ-APLY-004] 지원 승인 성공 (200 OK)"""
        url = reverse("recruiter-application-accept", kwargs={"application_id": self.application.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, ApplicationStatus.ACCEPTED)

    def test_application_accept_unauthorized(self) -> None:
        """지원 승인 - 인증 없음 (401 UNAUTHORIZED)"""
        self.client.force_authenticate(user=None)
        url = reverse("recruiter-application-accept", kwargs={"application_id": self.application.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_application_accept_permission_denied(self) -> None:
        """지원 승인 - 권한 없음 (403 FORBIDDEN)"""
        self.client.force_authenticate(user=self.other_author)
        url = reverse("recruiter-application-accept", kwargs={"application_id": self.application.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)

    def test_application_accept_not_found(self) -> None:
        """지원 승인 - 지원 내역 없음 (404 NOT FOUND)"""
        url = reverse("recruiter-application-accept", kwargs={"application_id": 99999})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error_detail", response.data)

    def test_application_reject_success(self) -> None:
        """[REQ-APLY-005] 지원 거절 성공 (200 OK)"""
        url = reverse("recruiter-application-reject", kwargs={"application_id": self.application.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, ApplicationStatus.REJECTED)

    def test_application_reject_unauthorized(self) -> None:
        """지원 거절 - 인증 없음 (401 UNAUTHORIZED)"""
        self.client.force_authenticate(user=None)
        url = reverse("recruiter-application-reject", kwargs={"application_id": self.application.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_application_reject_permission_denied(self) -> None:
        """지원 거절 - 권한 없음 (403 FORBIDDEN)"""
        self.client.force_authenticate(user=self.other_author)
        url = reverse("recruiter-application-reject", kwargs={"application_id": self.application.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)

    def test_application_reject_not_found(self) -> None:
        """지원 거절 - 지원 내역 없음 (404 NOT FOUND)"""
        url = reverse("recruiter-application-reject", kwargs={"application_id": 99999})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error_detail", response.data)

    def test_application_list_with_cursor_pagination(self) -> None:
        """목록 조회 - 커서 페이지네이션 동작 확인"""
        another_applicant = User.objects.create(
            email="applicant2@test.com",
            nickname="applicant2",
            name="지원자2",
            phone_number="01044445555",
            birthday="1990-01-01",
            gender="M",
        )
        another_applicant.set_password("testpassword1")
        another_applicant.save()

        Application.objects.create(
            recruitment=self.recruitment,
            applicant=another_applicant,
            self_introduction="지원자2",
            motivation="동기2",
            objective="목표2",
            available_time="12:00 ~ 13:00",
            has_study_experience=False,
            study_experience="",
            status=ApplicationStatus.PENDING,
        )

        url = reverse("recruiter-application-list", kwargs={"recruitment_uuid": self.recruitment.uuid})
        response = self.client.get(url, {"page_size": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)

    def test_application_accept_already_processed(self) -> None:
        """지원 승인 - 이미 처리된 지원 (400 BAD REQUEST)"""
        self.application.status = ApplicationStatus.ACCEPTED
        self.application.save()

        url = reverse("recruiter-application-accept", kwargs={"application_id": self.application.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertEqual(response.data["error_detail"], "이미 처리된 지원입니다.")

    def test_application_accept_headcount_exceeded(self) -> None:
        """지원 승인 - 모집 인원 초과 (400 BAD REQUEST)"""
        for i in range(5):
            applicant = User.objects.create(
                email=f"applicant{i}@test.com",
                nickname=f"applicant{i}",
                name=f"지원자{i}",
                phone_number=f"0105555{i:04d}",
                birthday="1990-01-01",
                gender="M",
            )
            Application.objects.create(
                recruitment=self.recruitment,
                applicant=applicant,
                self_introduction=f"자기소개{i}",
                motivation=f"동기{i}",
                objective=f"목표{i}",
                available_time="10:00 ~ 11:00",
                has_study_experience=True,
                study_experience=f"경험{i}",
                status=ApplicationStatus.ACCEPTED,
            )

        url = reverse("recruiter-application-accept", kwargs={"application_id": self.application.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertEqual(response.data["error_detail"], "모집 인원이 초과되었습니다.")

    def test_application_reject_already_processed(self) -> None:
        """지원 거절 - 이미 처리된 지원 (400 BAD REQUEST)"""
        self.application.status = ApplicationStatus.REJECTED
        self.application.save()

        url = reverse("recruiter-application-reject", kwargs={"application_id": self.application.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertEqual(response.data["error_detail"], "이미 처리된 지원입니다.")
