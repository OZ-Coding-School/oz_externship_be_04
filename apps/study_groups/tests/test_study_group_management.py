from datetime import date, datetime, timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import make_aware, now
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory

from apps.lectures.models import CrawledLecture
from apps.study_groups.models import GroupMember, Review, StudyGroup, StudyLecture
from apps.study_groups.serializers.study_group import (
    StudyGroupDetailSerializer,
    StudyGroupListSerializer,
    StudyGroupSerializer,
)
from apps.study_groups.services.study_group_service import retrieve_study_group

UserModel = get_user_model()


# 스터디그룹 생성 관련
class StudyGroupCreationTests(TestCase):

    def setUp(self) -> None:
        self.user = UserModel.objects.create(
            nickname="leader1",
            email="leader1@example.com",
            birthday=date(2000, 1, 1),
            phone_number="01000000001",
        )
        self.user.set_password("qwer1234")
        self.user.save()

        self.client: Any = APIClient()
        self.client.force_authenticate(user=self.user)

        # 테스트용 강의 생성
        self.lecture1 = CrawledLecture.objects.create(
            title="강의1",
            instructor="강사1",
            external_id="1",
            average_rating=0.0,
            total_class_time=0,
            difficulty="EASY",
            description="테스트 강의1",
            platform="INFLEARN",
            url_link="https://example.com/lecture1",
            thumbnail_img_url="https://example.com/thumb1.jpg",
        )
        self.lecture2 = CrawledLecture.objects.create(
            title="강의2",
            instructor="강사2",
            external_id="2",
            average_rating=0.0,
            total_class_time=0,
            difficulty="EASY",
            description="테스트 강의2",
            platform="INFLEARN",
            url_link="https://example.com/lecture2",
            thumbnail_img_url="https://example.com/thumb2.jpg",
        )

    def test_create_study_group_success(self) -> None:
        url = reverse("study-group-list-create")
        data = {
            "name": "알고리즘 스터디",
            "introduction": "코테 대비 스터디입니다",
            "max_headcount": 5,
            "start_at": (now() + timedelta(days=1)).isoformat(),
            "end_at": (now() + timedelta(days=10)).isoformat(),
            "lectures": [self.lecture1.id, self.lecture2.id],
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(StudyGroup.objects.count(), 1)

        study_group = StudyGroup.objects.first()
        assert study_group is not None
        self.assertEqual(study_group.name, "알고리즘 스터디")
        self.assertEqual(study_group.introduction, "코테 대비 스터디입니다")
        self.assertEqual(study_group.max_headcount, 5)

        # 리더 자동 생성 확인
        self.assertTrue(
            GroupMember.objects.filter(
                study_group_id=study_group.id,
                user_id=self.user.id,
                is_leader=True,
            ).exists()
        )

    # 강의 없이 스터디그룹 생성
    def test_create_study_group_without_lectures(self) -> None:
        url = reverse("study-group-list-create")
        data = {
            "name": "독서 스터디",
            "introduction": "책 읽기 스터디",
            "max_headcount": 3,
            "start_at": (now() + timedelta(days=1)).isoformat(),
            "end_at": (now() + timedelta(days=10)).isoformat(),
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(StudyGroup.objects.count(), 1)

    # 비로그인 사용자 스터디그룹 생성
    def test_create_study_group_unauthorized(self) -> None:

        self.client.force_authenticate(user=None)
        url = reverse("study-group-list-create")
        data = {
            "name": "알고리즘 스터디",
            "max_headcount": 5,
            "start_at": (now() + timedelta(days=1)).isoformat(),
            "end_at": (now() + timedelta(days=10)).isoformat(),
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 401)

    # 과거 날짜로 시작일 설정
    def test_create_study_group_invalid_start_date(self) -> None:
        url = reverse("study-group-list-create")
        # 어제 날짜 에러
        yesterday_date = now().date() - timedelta(days=1)
        yesterday_datetime = now().replace(
            year=yesterday_date.year,
            month=yesterday_date.month,
            day=yesterday_date.day,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        data = {
            "name": "알고리즘 스터디",
            "max_headcount": 5,
            "start_at": yesterday_datetime.isoformat(),
            "end_at": (now() + timedelta(days=10)).isoformat(),
        }

        response: Response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("시작일은 오늘 이후여야 합니다", str(response.data))

    # 스터디 기간이 5일 미만
    def test_create_study_group_invalid_end_date(self) -> None:
        url = reverse("study-group-list-create")
        data = {
            "name": "알고리즘 스터디",
            "max_headcount": 5,
            "start_at": (now() + timedelta(days=1)).isoformat(),
            "end_at": (now() + timedelta(days=3)).isoformat(),
        }

        response: Response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("종료일은 시작일보다 최소 5일 이후여야 합니다", str(response.data))

    # 강의 5개 초과 선택
    def test_create_study_group_too_many_lectures(self) -> None:
        # 추가 강의 생성
        lectures = []
        for i in range(6):
            lecture = CrawledLecture.objects.create(
                title=f"강의{i+3}",
                instructor=f"강사{i+3}",
                external_id=str(i + 3),
                average_rating=0.0,
                total_class_time=0,
            )
            lectures.append(lecture.id)

        url = reverse("study-group-list-create")
        data = {
            "name": "알고리즘 스터디",
            "max_headcount": 5,
            "start_at": (now() + timedelta(days=1)).isoformat(),
            "end_at": (now() + timedelta(days=10)).isoformat(),
            "lectures": lectures,
        }

        response: Response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("5", str(response.data))

    # 존재하지 않는 강의 ID
    def test_create_study_group_invalid_lecture_id(self) -> None:
        url = reverse("study-group-list-create")
        data = {
            "name": "알고리즘 스터디",
            "max_headcount": 5,
            "start_at": (now() + timedelta(days=1)).isoformat(),
            "end_at": (now() + timedelta(days=10)).isoformat(),
            "lectures": [99999],  # 존재하지 않는 ID
        }

        response: Response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("존재하지 않는 강의 ID", str(response.data))

    # max_headcount 범위 미만, 초과
    def test_create_study_group_invalid_max_headcount(self) -> None:
        url = reverse("study-group-list-create")
        data = {
            "name": "알고리즘 스터디",
            "max_headcount": 1,  # 최소값 2 미만
            "start_at": (now() + timedelta(days=1)).isoformat(),
            "end_at": (now() + timedelta(days=10)).isoformat(),
        }

        response = self.client.post(url, data, format="json")

        # DB constraint 위반으로 인한 에러
        self.assertIn(response.status_code, [400, 500])

    # 중복된 스터디그룹명
    def test_create_study_group_duplicate_name(self) -> None:
        StudyGroup.objects.create(
            name="알고리즘 스터디",
            max_headcount=5,
            start_at=now() + timedelta(days=1),
            end_at=now() + timedelta(days=10),
        )

        url = reverse("study-group-list-create")
        data = {
            "name": "알고리즘 스터디",  # 중복된 이름
            "max_headcount": 5,
            "start_at": (now() + timedelta(days=1)).isoformat(),
            "end_at": (now() + timedelta(days=10)).isoformat(),
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 400)


# 스터디그룹 RUD
class StudyGroupManagementTests(TestCase):

    def setUp(self) -> None:
        self.leader = UserModel.objects.create(
            nickname="leader",
            email="leader@example.com",
            name="리더",
            birthday=date(2000, 1, 1),
            phone_number="01000000001",
            gender="M",
        )
        self.leader.set_password("qwer1234")
        self.leader.save()

        self.member1 = UserModel.objects.create(
            nickname="member1",
            email="member1@example.com",
            name="멤버1",
            birthday=date(2000, 1, 1),
            phone_number="01000000002",
            gender="M",
        )
        self.member1.set_password("qwer1234")
        self.member1.save()

        self.member2 = UserModel.objects.create(
            nickname="member2",
            email="member2@example.com",
            name="멤버2",
            birthday=date(2000, 1, 1),
            phone_number="01000000003",
            gender="M",
        )
        self.member2.set_password("qwer1234")
        self.member2.save()

        # 테스트용 강의 생성
        self.lecture1 = CrawledLecture.objects.create(
            title="강의1",
            instructor="강사1",
            external_id="1",
            average_rating=0.0,
            total_class_time=0,
            difficulty="EASY",
            description="테스트 강의1",
            platform="INFLEARN",
            url_link="https://example.com/lecture1",
            thumbnail_img_url="https://example.com/thumb1.jpg",
        )
        self.lecture2 = CrawledLecture.objects.create(
            title="강의2",
            instructor="강사2",
            external_id="2",
            average_rating=0.0,
            total_class_time=0,
            difficulty="EASY",
            description="테스트 강의2",
            platform="INFLEARN",
            url_link="https://example.com/lecture2",
            thumbnail_img_url="https://example.com/thumb2.jpg",
        )

        self.study_group = StudyGroup.objects.create(
            name="테스트 스터디",
            max_headcount=5,
            start_at=now() + timedelta(days=1),
            end_at=now() + timedelta(days=10),
        )

        GroupMember.objects.create(
            study_group_id=self.study_group,
            user_id=self.leader,
            is_leader=True,
        )
        GroupMember.objects.create(
            study_group_id=self.study_group,
            user_id=self.member1,
            is_leader=False,
        )
        GroupMember.objects.create(
            study_group_id=self.study_group,
            user_id=self.member2,
            is_leader=False,
        )

        self.leader_client: Any = APIClient()
        self.leader_client.force_authenticate(user=self.leader)

        self.member_client: Any = APIClient()
        self.member_client.force_authenticate(user=self.member1)

    # 리더가 스터디그룹 수정
    def test_update_study_group_by_leader_success(self) -> None:
        url = reverse("study-group-rud", args=[self.study_group.id])
        data = {
            "name": "수정된 스터디 이름",
            "introduction": "수정된 소개",
        }

        response = self.leader_client.patch(url, data, format="json")

        self.assertEqual(response.status_code, 200)
        self.study_group.refresh_from_db()
        self.assertEqual(self.study_group.name, "수정된 스터디 이름")
        self.assertEqual(self.study_group.introduction, "수정된 소개")

    # 일반 멤버 스터디그룹 수정
    ### 유효성 추가 필요 (막아야함...)
    def test_update_study_group_by_member_success(self) -> None:
        url = reverse("study-group-rud", args=[self.study_group.id])
        data = {
            "name": "멤버가 수정한 이름",
        }

        response = self.member_client.patch(url, data, format="json")

        self.assertEqual(response.status_code, 200)

    # 리더가 스터디그룹 삭제 (정상)
    def test_delete_study_group_by_leader_success(self) -> None:
        url = reverse("study-group-rud", args=[self.study_group.id])

        response = self.leader_client.delete(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(StudyGroup.objects.filter(id=self.study_group.id).exists())
        self.assertFalse(GroupMember.objects.filter(study_group_id=self.study_group.id).exists())

    # 일반 멤버가 스터디그룹 삭제
    def test_delete_study_group_by_member_forbidden(self) -> None:
        url = reverse("study-group-rud", args=[self.study_group.id])

        response: Response = self.member_client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertIn("스터디 그룹 삭제 권한이 없습니다", response.data["error_detail"])
        # 스터디그룹 삭제 실패?
        self.assertTrue(StudyGroup.objects.filter(id=self.study_group.id).exists())

    # 스터디그룹 수정 (강의 업데이트)
    ### 서비스에서 lectures 처리 추가 필요? -> 임시로 시리얼라이저 직접 이용함
    def test_update_study_group_with_lectures(self) -> None:
        # 기존 강의 추가
        StudyLecture.objects.create(
            study_group=self.study_group,
            lecture=self.lecture1,
        )

        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.patch("/")
        request.user = self.leader

        serializer = StudyGroupSerializer(
            self.study_group,
            data={"lectures": [self.lecture2.id]},
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 기존 강의 삭제 + 새로운 강의만
        self.assertEqual(StudyLecture.objects.filter(study_group=self.study_group).count(), 1)
        self.assertTrue(
            StudyLecture.objects.filter(
                study_group=self.study_group,
                lecture=self.lecture2,
            ).exists()
        )

    # 스터디그룹 수정 시 강의 제거
    ### 서비스에서 lectures 처리 추가 필요? -> 임시로 시리얼라이저 직접 이용함
    def test_update_study_group_remove_lectures(self) -> None:
        # 기존 강의 추가
        StudyLecture.objects.create(
            study_group=self.study_group,
            lecture=self.lecture1,
        )

        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.patch("/")
        request.user = self.leader

        serializer = StudyGroupSerializer(
            self.study_group,
            data={"lectures": []},
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertEqual(StudyLecture.objects.filter(study_group=self.study_group).count(), 0)

    # 스터디그룹 상세 조회
    ### 추가 필요? -> 임시로 시리얼라이저 직접 이용함
    def test_retrieve_study_group_detail(self) -> None:
        # 강의 추가
        StudyLecture.objects.create(
            study_group=self.study_group,
            lecture=self.lecture1,
        )

        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.leader

        study_group = retrieve_study_group(group_id=self.study_group.id, user=self.leader)
        serializer = StudyGroupDetailSerializer(study_group, context={"request": request})

        # 실제 에러
        try:
            data = serializer.data
        except Exception as e:
            self.fail(f"Serializer error: {type(e).__name__}: {str(e)}")

        self.assertIn("lectures", data)
        self.assertIn("members", data)
        self.assertIn("current_headcount", data)
        members = data["members"]
        self.assertEqual(len(members), 3)  # leader, member1, member2
        self.assertTrue(members[0]["is_leader"])

    # 스터디그룹 목록 조회
    def test_list_study_groups_with_serializer(self) -> None:
        # 강의 추가
        StudyLecture.objects.create(
            study_group=self.study_group,
            lecture=self.lecture1,
        )

        url = reverse("study-group-list-create")
        response: Response = self.leader_client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        if len(response.data) > 0:
            group_data = response.data[0]
            self.assertIn("lectures", group_data)
            self.assertIn("current_headcount", group_data)
            self.assertIn("is_leader", group_data)
            self.assertIn("reviews", group_data)

    # 비로그인 스터디그룹 목록 조회
    def test_list_study_groups_unauthenticated(self) -> None:
        unauthenticated_client: Any = APIClient()
        url = reverse("study-group-list-create")
        response = unauthenticated_client.get(url)

        self.assertEqual(response.status_code, 401)

    # 일반 멤버가 목록 조회 -> is_leader 확인
    def test_list_study_groups_is_leader_false(self) -> None:
        url = reverse("study-group-list-create")
        response: Response = self.member_client.get(url)

        self.assertEqual(response.status_code, 200)
        for group_data in response.data:
            if group_data["id"] == self.study_group.id:
                self.assertFalse(group_data["is_leader"])
                break

    # validate_lectures / len(value) > 5
    # serializer 직접 사용
    def test_validate_lectures_length_direct(self) -> None:

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.leader

        serializer = StudyGroupSerializer(context={"request": request})
        # 6개의 강의 ID로 직접 검증 메서드 호출
        with self.assertRaises(Exception) as context:
            serializer.validate_lectures([1, 2, 3, 4, 5, 6])

        self.assertIn("강의는 최대 5개까지 선택 가능합니다", str(context.exception))

    # create 메서드에서 강의 있음 (serializer 직접 사용)
    def test_create_with_lectures_data(self) -> None:
        # view에서 서비스를 사용하므로 serializer의 create를 직접 테스트
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.post("/")
        request.user = self.leader

        data = {
            "name": "강의 포함 스터디",
            "introduction": "강의가 포함된 스터디",
            "max_headcount": 5,
            "start_at": (now() + timedelta(days=1)).isoformat(),
            "end_at": (now() + timedelta(days=10)).isoformat(),
            "lectures": [self.lecture1.id, self.lecture2.id],
        }

        serializer = StudyGroupSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        study_group = serializer.save()

        self.assertEqual(
            StudyLecture.objects.filter(study_group=study_group).count(),
            2,
        )
