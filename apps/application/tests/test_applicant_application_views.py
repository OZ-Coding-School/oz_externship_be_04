from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.application.models import Application, ApplicationStatus
from apps.recruitment.models import Recruitment
from apps.study_groups.models import StudyGroup
from apps.users.models import User


class ApplicantApplicationAPITestCase(APITestCase):
    """지원/조회/취소 API 통합 테스트"""

    def setUp(self) -> None:
        """테스트 기본 데이터 생성"""

        # 테스트 수행할 로그인 유저 생성
        self.applicant = User.objects.create(
            email="applicant@test.com",
            nickname="applicant",
            name="지원자",
            phone_number="01011112222",
            birthday="1990-01-01",
            gender="M",
        )
        self.applicant.set_password("testpassword1")
        self.applicant.save()

        # 공고 작성할 다른 유저 생성
        self.author = User.objects.create(
            email="author@test.com",
            nickname="author",
            name="작성자",
            phone_number="01033334444",
            birthday="1990-01-01",
            gender="F",
        )
        self.author.set_password("testpassword1")
        self.author.save()

        self.client.force_authenticate(user=self.applicant)

        # StudyGroup 생성
        self.study_group = StudyGroup.objects.create(
            name="테스트 스터디",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now(),
        )

        # Recruitment 생성
        self.recruitment = Recruitment.objects.create(
            author=self.author,
            study_group=self.study_group,
            title="테스트 공고",
            content="테스트 내용",
            estimated_fee=10000,
            expected_headcount=5,
            close_at=timezone.now(),
        )

        # 사전 지원 내역 생성 (조회/취소 테스트용)
        self.existing_application = Application.objects.create(
            recruitment=self.recruitment,
            applicant=self.applicant,
            self_introduction="소개",
            motivation="동기",
            objective="목표",
            available_time="시간",
            has_study_experience=False,
            study_experience="",
            status=ApplicationStatus.PENDING,
        )

        # 지원서 제출 페이로드
        self.application_payload = {
            "self_introduction": "새로운 소개",
            "motivation": "새로운 동기",
            "objective": "새로운 목표",
            "available_time": "주 5회",
            "has_study_experience": True,
            "study_experience": "경험 있음",
        }

    # 지원서 제출 테스트 (REQ-APLY-001)
    def test_application_create_success(self) -> None:
        """본인이 작성하지 않은 공고에 지원 성공 (201 CREATED)"""

        new_recruitment = Recruitment.objects.create(
            author=self.author,
            study_group=self.study_group,
            title="새 공고",
            close_at=timezone.now(),
            estimated_fee=20000,
            expected_headcount=5,
        )

        url = reverse("application-create", kwargs={"recruitment_uuid": new_recruitment.uuid})

        response = self.client.post(url, data=self.application_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Application.objects.count(), 2)

    def test_application_create_already_applied(self) -> None:
        """이미 지원한 공고에 재지원 시도 (409 CONFLICT)"""

        url = reverse("application-create", kwargs={"recruitment_uuid": self.recruitment.uuid})

        response = self.client.post(url, data=self.application_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Application.objects.count(), 1)
        self.assertIn("이미 지원한 내역이 존재합니다.", response.data["error_detail"])

    # 내가 지원한 목록 조회 테스트 (REQ-APLY-006)
    def test_my_application_list_with_pagination(self) -> None:
        """내 지원 목록 조회 - 커서 페이지네이션 동작 테스트"""

        for i in range(5):
            new_recruit = Recruitment.objects.create(
                author=self.author,
                study_group=self.study_group,
                title=f"페이지네이션 공고{i}",
                content="내용",
                estimated_fee=10000,
                expected_headcount=5,
                close_at=timezone.now(),
            )

            Application.objects.create(
                recruitment=new_recruit,
                applicant=self.applicant,
                self_introduction=f"소개 {i}",
                motivation=f"동기 {i}",
                objective="목표",
                available_time="시간",
                has_study_experience=False,
                study_experience="",
            )

        url = reverse("application-list-mine") + "?page_size=2"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("next", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)

        next_cursor = response.data["next"]
        self.assertIsNotNone(next_cursor)

        resp2 = self.client.get(next_cursor)
        self.assertEqual(len(resp2.data["results"]), 2)

        next_cursor2 = resp2.data["next"]
        resp3 = self.client.get(next_cursor2)
        self.assertEqual(len(resp3.data["results"]), 2)

    # 내가 지원한 상세 조회 테스트 (REQ-APLY-007)
    def test_my_application_detail_success(self) -> None:
        """내 지원 상세 조회 성공 (200 OK)"""

        url = reverse("application-detail", kwargs={"application_uuid": self.existing_application.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["uuid"], str(self.existing_application.uuid))
        self.assertEqual(response.data["motivation"], "동기")

    def test_my_application_detail_not_owner(self) -> None:
        """다른 사람의 지원서 조회 시도 (404 NOT FOUND)"""

        other_application = Application.objects.create(
            recruitment=self.recruitment,
            applicant=self.author,
            self_introduction="다른사람의 소개",
            motivation="다른사람의 동기",
        )
        url = reverse("application-detail", kwargs={"application_uuid": other_application.uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 지원 취소 테스트 (REQ-APLY-008)
    def test_application_cancel_success(self) -> None:
        """지원 취소 성공 (200 OK)"""

        url = reverse("application-cancel", kwargs={"application_uuid": self.existing_application.uuid})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "지원 내역이 취소되었습니다.")

        self.existing_application.refresh_from_db()
        self.assertEqual(self.existing_application.status, ApplicationStatus.CANCELED)

    def test_application_cancel_not_found(self) -> None:
        """존재하지 않는 지원 내역 취소 테스트 (404 NOT FOUND)"""

        url = "/api/v1/applications/00000000-0000-0000-0000-000000000000/cancel"
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "해당 지원서를 찾을 수 없습니다.")
