from typing import Any, Dict, List, TypedDict

from django.db import transaction

from apps.lectures.models.category import Category, LectureCategory
from apps.lectures.models.crawled_lecture import CrawledLecture
from apps.lectures.models.crawled_lecture_review import CrawledLectureReview


class SyncResult(TypedDict):
    created_lectures: int
    updated_lectures: int
    created_reviews: int


@transaction.atomic
def sync_inflearn_db(final_results: List[Dict[str, Any]]) -> SyncResult:
    platform_name = "INFLEARN"
    # 크롤링 결과에서 모든 강의 id 수집
    external_ids = [str(item["id"]) for item in final_results]

    lecture_map: dict[str, CrawledLecture] = {
        str(lec.external_id): lec
        for lec in CrawledLecture.objects.filter(
            platform=platform_name,
            external_id__in=external_ids,
        )
    }
    # 새로 생성할 강의 + 업데이트 할 강의 목록
    create_list: list[CrawledLecture] = []
    update_list: list[CrawledLecture] = []

    for item in final_results:
        external_id = str(item["id"])
        # 카테고리 저장
        for c in item.get("categories", []):
            Category.objects.get_or_create(name=c["name"])
        # crawled_lecture필드에 들어갈 기본값
        defaults = {
            "external_id": external_id,
            "title": item.get("title", ""),
            "instructor": item.get("instructor") or "",
            "average_rating": item.get("average_rating", 0),
            "total_class_time": item.get("total_class_time", 0),
            "difficulty": item.get("difficulty", ""),
            "description": item.get("description") or "",
            "platform": platform_name,
            "original_price": item.get("original_price", 0),
            "discount_price": item.get("discount_price", 0),
            "url_link": item.get("url_link", ""),
            "thumbnail_img_url": item.get("thumbnail_img_url") or "",
        }
        # 존재하면 값만 갱신(bulk_up), 존재하지 않으면 새로 생성(bulk_cr)
        obj = lecture_map.get(external_id)

        if obj:
            for k, v in defaults.items():
                setattr(obj, k, v)
            update_list.append(obj)
        else:
            create_list.append(CrawledLecture(**defaults))
    # 생성 대상이 있으면 중복 제거
    if create_list:
        unique_map: dict[tuple[str, str], CrawledLecture] = {}
        for obj in create_list:
            unique_map[(obj.platform, str(obj.external_id))] = obj
        create_list = list(unique_map.values())
        # 신규 강의 생성
        CrawledLecture.objects.bulk_create(
            create_list,
            batch_size=500,
            ignore_conflicts=True,
        )
    if update_list:
        CrawledLecture.objects.bulk_update(
            update_list,
            fields=[
                "title",
                "instructor",
                "average_rating",
                "total_class_time",
                "difficulty",
                "description",
                "original_price",
                "discount_price",
                "url_link",
                "thumbnail_img_url",
            ],
            batch_size=500,
        )
    # 리뷰가 삭제될 수도 있어서 전체 삭제 후 교체
    CrawledLectureReview.objects.filter(lecture__platform=platform_name).delete()
    # 최신 강의 조회
    lecture_map = {
        str(lec.external_id): lec
        for lec in CrawledLecture.objects.filter(
            platform=platform_name,
            external_id__in=external_ids,
        )
    }

    LectureCategory.objects.filter(lecture__platform=platform_name).delete()

    category_map = {c.name: c for c in Category.objects.all()}
    lecture_category_objs: list[LectureCategory] = []

    for item in final_results:
        lecture = lecture_map.get(str(item["id"]))
        if lecture is None:
            continue

        for c in item.get("categories", []):
            category = category_map.get(c["name"])
            if category is None:
                continue

            lecture_category_objs.append(
                LectureCategory(
                    lecture=lecture,
                    category=category,
                )
            )

    if lecture_category_objs:
        LectureCategory.objects.bulk_create(
            lecture_category_objs,
            batch_size=1000,
            ignore_conflicts=True,
        )

    CrawledLectureReview.objects.filter(lecture__platform=platform_name).delete()

    review_objs: list[CrawledLectureReview] = []

    for item in final_results:
        lecture = lecture_map.get(str(item["id"]))
        if lecture is None:
            continue
        # 비어있는 리뷰 제거
        for r in item.get("reviews", []):
            content = (r.get("content") or "").strip()
            if not content:
                continue

            review_objs.append(
                CrawledLectureReview(
                    lecture=lecture,
                    external_id=r.get("id", ""),
                    rating=r.get("rating", 0),
                    content=content,
                )
            )

    if review_objs:
        CrawledLectureReview.objects.bulk_create(
            review_objs,
            batch_size=500,
            ignore_conflicts=True,
        )

    return {
        "created_lectures": len(create_list),
        "updated_lectures": len(update_list),
        "created_reviews": len(review_objs),
    }
