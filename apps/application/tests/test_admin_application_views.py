import uuid
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.application.models import Application, ApplicationStatus
from apps.recruitment.models import Recruitment
from apps.study_groups.models import StudyGroup
from apps.users.models import User


class AdminApplicationAPITestCase(APITestCase):
    """
    (Admin) 지원 내역 목록/상세 조회 API 테스트
    - AdminApplicationListView
    - AdminApplicationDetailView
    """

    def setUp(self) -> None:
        # 관리자 유저 생성
        self.admin_user = User.objects.create(
            email="admin@test.com",
            nickname="admin",
            name="관리자",
            phone_number="01011112222",
            birthday="1990-01-01",
            gender="M",
        )
        self.admin_user.set_password("adminpassword")
        self.admin_user.is_staff = True
        self.admin_user.save()

        # 일반 유저 생성
        self.normal_user = User.objects.create(
            email="user@test.com",
            nickname="user",
            name="일반유저",
            phone_number="01033334444",
            birthday="1995-01-01",
            gender="F",
        )
        self.normal_user.set_password("userpassword")
        self.normal_user.save()

        # 스터디 그룹 생성
        self.study_group = StudyGroup.objects.create(
            name="테스트 스터디",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now(),
        )

        # Djang와 Python 2가지 모집 공고 생성
        self.recruitment_python = Recruitment.objects.create(
            author=self.admin_user,
            study_group=self.study_group,
            title="파이썬 스터디 모집합니다",
            content="파이썬 내용입니다",
            estimated_fee=10000,
            expected_headcount=5,
            close_at=timezone.now(),
        )

        self.recruitment_django = Recruitment.objects.create(
            author=self.admin_user,
            study_group=self.study_group,
            title="Django 스터디 모집합니다",
            content="장고 내용입니다",
            estimated_fee=20000,
            expected_headcount=3,
            close_at=timezone.now(),
        )

        # 지원서 생성(3개)
        self.app1 = Application.objects.create(
            recruitment=self.recruitment_python,
            applicant=self.normal_user,
            self_introduction="소개1",
            motivation="동기1",
            objective="목표1",
            available_time="주 2회",
            has_study_experience=False,
            study_experience="",
            status=ApplicationStatus.PENDING,
        )

        self.app2 = Application.objects.create(
            recruitment=self.recruitment_python,
            applicant=self.admin_user,
            self_introduction="소개2",
            motivation="동기2",
            objective="목표2",
            available_time="주 3회",
            has_study_experience=True,
            study_experience="경험 있음",
            status=ApplicationStatus.ACCEPTED,
        )

        self.app3 = Application.objects.create(
            recruitment=self.recruitment_django,
            applicant=self.normal_user,
            self_introduction="소개3",
            motivation="동기3",
            objective="목표3",
            available_time="주 1회",
            has_study_experience=False,
            study_experience="",
            status=ApplicationStatus.REJECTED,
        )

        self.client.force_authenticate(user=self.admin_user)

        self.list_url = "/api/v1/admin/applications"

    def test_admin_application_list_success(self) -> None:
        """
        (Admin) 지원 내역 목록 조회 성공
        """
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 3)

    def test_non_admin_cannot_access_admin_application_list(self) -> None:
        """
        (Admin) 비관리자 접근 차단 (403 FORBIDDEN)
        """
        self.client.force_authenticate(user=self.normal_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_application_list_filter_by_status(self) -> None:
        """
        (Admin) status 필터링
        """
        response = self.client.get(self.list_url, {"status": ApplicationStatus.ACCEPTED})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["status"], ApplicationStatus.ACCEPTED)

    def test_admin_application_list_search_by_recruitment_title(self) -> None:
        """
        (Admin) recruitment_title 로 공고 제목 검색
        """
        response = self.client.get(self.list_url, {"search": "파이썬"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        for item in response.data["results"]:
            self.assertIn("recruitment", item)
            self.assertIn("title", item["recruitment"])
            self.assertIn("파이썬", item["recruitment"]["title"])

    def test_admin_application_list_search_by_applicant_nickname(self) -> None:
        """
        (Admin) applicant_nickname 으로 지원자 닉네임 검색
        """
        response = self.client.get(self.list_url, {"search": "user"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        for item in response.data["results"]:
            self.assertIn("applicant", item)
            self.assertEqual(item["applicant"]["nickname"], "user")

    def test_admin_application_list_sort_latest_and_oldest(self) -> None:
        """
        (Admin) sort(latest, oldest) 정렬 테스트
        """
        Application.objects.filter(pk=self.app1.pk).update(created_at=timezone.now() - timedelta(days=2))
        Application.objects.filter(pk=self.app2.pk).update(created_at=timezone.now() - timedelta(days=1))
        Application.objects.filter(pk=self.app3.pk).update(created_at=timezone.now())

        # 최신순(3, 2, 1)
        response_latest = self.client.get(self.list_url, {"sort": "latest"})
        self.assertEqual(response_latest.status_code, status.HTTP_200_OK)
        latest_first_uuid = response_latest.data["results"][0]["uuid"]
        self.assertEqual(latest_first_uuid, str(self.app3.uuid))

        # 오래된 순(1, 2, 3)
        response_oldest = self.client.get(self.list_url, {"sort": "oldest"})
        self.assertEqual(response_oldest.status_code, status.HTTP_200_OK)
        oldest_first_uuid = response_oldest.data["results"][0]["uuid"]
        self.assertEqual(oldest_first_uuid, str(self.app1.uuid))

    def test_admin_application_detail_success(self) -> None:
        """
        (Admin) 지원 내역 상세 조회 성공 (200 OK)
        """
        url = f"/api/v1/admin/applications/{self.app1.uuid}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["uuid"], str(self.app1.uuid))
        self.assertEqual(response.data["motivation"], self.app1.motivation)
        self.assertIn("recruitment", response.data)
        self.assertIn("applicant", response.data)

    def test_admin_application_detail_not_found(self) -> None:
        """
        (Admin) 존재하지 않는 지원 내역 조회 시 404 NOT FOUND
        """
        random_uuid = uuid.uuid4()
        url = f"/api/v1/admin/applications/{random_uuid}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "해당 지원서를 찾을 수 없습니다.")

    def test_non_admin_cannot_access_admin_application_detail(self) -> None:
        """
        (Admin) 비관리자는 상세 조회 불가 (403 FORBIDDEN)
        """
        self.client.force_authenticate(user=self.normal_user)

        url = f"/api/v1/admin/applications/{self.app1.uuid}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
