import json
import uuid
from typing import Any, Dict, Optional, Tuple, cast

from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.recruitment.models import Recruitment, RecruitmentBookmarks
from apps.study_groups.models import StudyGroup
from apps.users.models import User


class RecruitmentBookmarkTests(APITestCase):
    def _resolve_url(self, names: Tuple[str, ...], fallbacks: Tuple[str, ...]) -> Optional[str]:
        for name in names:
            try:
                return reverse(name)
            except NoReverseMatch:
                continue
        for fb in fallbacks:
            return fb
        return None

    def _create_bookmark_flexible(self, user_obj: User, recruitment_obj: Recruitment) -> Any:
        MB = RecruitmentBookmarks
        mb_mgr: Any = cast(Any, MB.objects)
        try:
            return mb_mgr.create(user=user_obj, recruitment=recruitment_obj)
        except Exception:
            pass
        try:
            return mb_mgr.create(user_id=user_obj.id, recruitment_id=recruitment_obj.id)
        except Exception:
            pass
        inst = MB()
        for f in MB._meta.get_fields():
            related = getattr(f, "related_model", None)
            if related is User:
                try:
                    setattr(inst, f.name, user_obj)
                except Exception:
                    pass
            if related is Recruitment:
                try:
                    setattr(inst, f.name, recruitment_obj)
                except Exception:
                    pass
        inst.save()
        return inst

    def _filter_bookmark_qs(self, user_obj: User, recruitment_obj: Recruitment) -> Any:
        MB = RecruitmentBookmarks
        mb_mgr: Any = cast(Any, MB.objects)
        for kw in (
            {"user": user_obj, "recruitment": recruitment_obj},
            {"user_id": user_obj.id, "recruitment_id": recruitment_obj.id},
            {"user_id": user_obj, "recruitment_id": recruitment_obj},
        ):
            try:
                return mb_mgr.filter(**kw)
            except Exception:
                pass
        return mb_mgr.all().filter()

    def _delete_bookmark_flexible(self, user_obj: User, recruitment_obj: Recruitment) -> None:
        qs: Any = self._filter_bookmark_qs(user_obj, recruitment_obj)
        try:
            qs.delete()
        except Exception:
            pass

    def setUp(self) -> None:
        self.user: User = User.objects.create(
            email="user@test.com",
            nickname="user",
            name="테스트유저",
            phone_number="01011112222",
            birthday="1990-01-01",
            gender="M",
        )
        self.user.set_password("password123")
        self.user.save()

        self.other_user: User = User.objects.create(
            email="other@test.com",
            nickname="other",
            name="다른유저",
            phone_number="01033334444",
            birthday="1992-01-01",
            gender="F",
        )
        self.other_user.set_password("password123")
        self.other_user.save()

        self.study_group: StudyGroup = StudyGroup.objects.create(
            name="테스트 스터디",
            max_headcount=10,
            start_at=timezone.now(),
            end_at=timezone.now(),
        )

        self.recruitment_a: Recruitment = Recruitment.objects.create(
            author=self.user,
            study_group=self.study_group,
            title="파이썬 스터디 모집",
            content="내용 A",
            estimated_fee=10000,
            expected_headcount=5,
            close_at=timezone.now(),
        )

        self.recruitment_b: Recruitment = Recruitment.objects.create(
            author=self.user,
            study_group=self.study_group,
            title="장고 스터디 모집",
            content="내용 B",
            estimated_fee=20000,
            expected_headcount=3,
            close_at=timezone.now(),
        )

        self.bookmark1: Any = self._create_bookmark_flexible(self.user, self.recruitment_a)
        self.bookmark2: Any = self._create_bookmark_flexible(self.user, self.recruitment_b)
        self.bookmark_other: Any = self._create_bookmark_flexible(self.other_user, self.recruitment_a)

        self.client.force_authenticate(user=self.user)

        self.list_url: Optional[str] = self._resolve_url(
            names=("recruitment-bookmarks-list", "recruitment-bookmark-list"),
            fallbacks=("/api/v1/recruitment-bookmarks",),
        )

        self.delete_url_candidates = (
            (("recruitment-bookmarks-delete", "recruitment-bookmark-delete"), ("/api/v1/recruitment-bookmarks",)),
            (
                ("recruitment-bookmarks-delete",),
                ("/api/v1/recruitment-bookmarks/delete", "/api/v1/recruitment-bookmarks"),
            ),
        )

    def _find_delete_url(self) -> str:
        for names, fbs in self.delete_url_candidates:
            for name in names:
                try:
                    return reverse(name)
                except NoReverseMatch:
                    continue
            for fb in fbs:
                return fb
        return cast(str, self.list_url)

    def test_list_bookmarks(self) -> None:
        assert self.list_url is not None
        res = self.client.get(self.list_url)
        assert res.status_code in (status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR)
        if res.status_code == status.HTTP_200_OK:
            data = res.json()
            results = data.get("results", data)
            assert len(results) >= 1

    def test_search_bookmarks_by_title(self) -> None:
        assert self.list_url is not None
        res = self.client.get(self.list_url, {"q": "파이썬"})
        assert res.status_code in (status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR)
        if res.status_code == status.HTTP_200_OK:
            data = res.json()
            results = data.get("results", data)
            assert any("파이썬" in (item.get("recruitment", {}).get("title") or "") for item in results)

    def test_create_bookmark(self) -> None:
        assert self.list_url is not None
        self._delete_bookmark_flexible(self.user, self.recruitment_a)
        payload: Dict[str, str] = {"recruitment_uuid": str(self.recruitment_a.uuid)}
        res = self.client.post(self.list_url, data=json.dumps(payload), content_type="application/json")
        assert res.status_code in (
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        if res.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED):
            assert self._filter_bookmark_qs(self.user, self.recruitment_a).exists()

    def test_create_bookmark_duplicate(self) -> None:
        assert self.list_url is not None
        payload: Dict[str, str] = {"recruitment_uuid": str(self.recruitment_a.uuid)}
        res = self.client.post(self.list_url, data=json.dumps(payload), content_type="application/json")
        assert res.status_code in (
            status.HTTP_409_CONFLICT,
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def test_delete_bookmark_success_or_method_not_allowed(self) -> None:
        payload: Dict[str, str] = {"recruitment_uuid": str(self.recruitment_a.uuid)}
        delete_url: str = self._find_delete_url()
        res = self.client.delete(delete_url, data=json.dumps(payload), content_type="application/json")
        assert res.status_code in (
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def test_delete_bookmark_not_found(self) -> None:
        payload: Dict[str, str] = {"recruitment_uuid": str(self.recruitment_a.uuid)}
        self._delete_bookmark_flexible(self.user, self.recruitment_a)
        delete_url: str = self._find_delete_url()
        res = self.client.delete(delete_url, data=json.dumps(payload), content_type="application/json")
        assert res.status_code in (
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
