import random
from datetime import date
from pprint import pprint

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.lectures.models import Category, CrawledLecture
from apps.study_groups.models import GroupMember, StudyGroup, StudyLecture
from apps.users.models import User


class RecommendLecturesTest(APITestCase):
    def setUp(self) -> None:

        random.seed(42)

        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass",
            name="테스트유저",
            nickname="tester",
            phone_number="01012345678",
            gender="M",
            birthday=date(2000, 1, 1),
            is_active=True,
        )

        self.categories = [Category.objects.create(name=cat) for cat in ["Python", "Algorithm", "Network", "Django"]]

        self.lectures = []
        for i in range(10):
            lec = CrawledLecture.objects.create(
                external_id=i + 1,
                title=f"강의{i+1}",
                instructor=f"강사{i+1}",
                average_rating=4.0 + i * 0.1,
                total_class_time=10 + i,
                difficulty=random.choice(
                    [
                        CrawledLecture.DifficultyEnum.EASY,
                        CrawledLecture.DifficultyEnum.NORMAL,
                        CrawledLecture.DifficultyEnum.HARD,
                    ]
                ),
                description=f"설명{i+1}",
                platform=random.choice([CrawledLecture.PlatformEnum.INFLEARN, CrawledLecture.PlatformEnum.UDEMY]),
                original_price=10000 + i * 1000,
                discount_price=5000 + i * 500,
                url_link=f"https://example.com/{i+1}",
                thumbnail_img_url=f"https://example.com/{i+1}.png",
            )
            lec.categories.add(random.choice(self.categories))
            self.lectures.append(lec)

        self.group = StudyGroup.objects.create(
            name="test-group",
            introduction="intro",
            max_headcount=5,
            start_at="2024-01-01T00:00:00Z",
            end_at="2024-12-31T00:00:00Z",
        )
        GroupMember.objects.create(
            study_group_id=self.group,
            user_id=self.user,
        )
        for lec_id in [2, 4, 6]:
            StudyLecture.objects.create(
                lecture=self.lectures[lec_id],
                study_group=self.group,
            )

    def test_personalized_recommendation_excludes_enrolled(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/lectures/recommends?max_count=2")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        enrolled_ids = [self.lectures[i].id for i in [2, 4, 6]]
        returned_ids = [lec["id"] for lec in response.data]

        for eid in enrolled_ids:
            self.assertNotIn(eid, returned_ids)

    def test_random_when_user_vector_missing(self) -> None:
        StudyLecture.objects.all().delete()
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/lectures/recommends?max_count=3")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_invalid_max_count(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/lectures/recommends?max_count=abc")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_max_count_one(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/lectures/recommends?max_count=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_random_when_all_lectures_enrolled(
        self,
    ) -> None:
        for lec in self.lectures:
            StudyLecture.objects.create(lecture=lec, study_group=self.group)

        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/lectures/recommends?max_count=2")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        returned_ids = [lec["id"] for lec in response.data]

        for rid in returned_ids:
            self.assertIn(rid, [lec.id for lec in self.lectures])

    def test_build_user_vector_with_weighted_average(self) -> None:
        self.user.lecture_bookmarks_middle_table.add(self.lectures[0])
        self.user.prefer_categories_middle_table.add(self.categories[2])

        StudyLecture.objects.create(lecture=self.lectures[2], study_group=self.group)

        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/lectures/recommends?max_count=3")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        recommended_ids = [lec["id"] for lec in response.data]

        self.assertNotIn(self.lectures[2].id, recommended_ids)

        possible_expected_ids = [self.lectures[0].id, self.lectures[4].id]
        self.assertTrue(any(rid in possible_expected_ids for rid in recommended_ids))

    def test_build_user_vector_no_activities(self) -> None:
        StudyLecture.objects.all().delete()
        self.user.lecture_bookmarks_middle_table.clear()
        self.user.prefer_categories_middle_table.clear()

        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/lectures/recommends?max_count=1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
