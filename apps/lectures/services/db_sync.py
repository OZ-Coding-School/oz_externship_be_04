from typing import Any, Dict, List, TypedDict

from django.db import transaction

from apps.lectures.models.category import Category
from apps.lectures.models.crawled_lecture import CrawledLecture
from apps.lectures.models.crawled_lecture_review import CrawledLectureReview


class SyncResult(TypedDict):
    created_lectures: int
    updated_lectures: int
    created_reviews: int


@transaction.atomic
def sync_inflearn_db(final_results: List[Dict[str, Any]]) -> SyncResult:
    platform_name = "INFLEARN"

    created_lectures = 0
    updated_lectures = 0
    created_reviews = 0

    create_list = []
    update_list = []

    for item in final_results:
        external_id = item["id"]

        for c in item.get("categories", []):
            Category.objects.get_or_create(name=c["name"])

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
            "discount_price": item.get("discounted_price", 0),
            "url_link": item.get("url_link", ""),
            "thumbnail_img_url": item.get("thumbnail_img_url", ""),
        }

        obj = CrawledLecture.objects.filter(platform=platform_name, external_id=external_id).first()

        if obj:
            for key, value in defaults.items():
                setattr(obj, key, value)
            update_list.append(obj)
        else:
            create_list.append(CrawledLecture(**defaults))

    if create_list:
        CrawledLecture.objects.bulk_create(create_list, batch_size=500)
        created_lectures = len(create_list)

    if update_list:
        CrawledLecture.objects.bulk_update(
            update_list,
            fields=[
                "external_id",
                "title",
                "instructor",
                "average_rating",
                "total_class_time",
                "difficulty",
                "description",
                "platform",
                "original_price",
                "discount_price",
                "url_link",
                "thumbnail_img_url",
            ],
            batch_size=500,
        )
        updated_lectures = len(update_list)

    CrawledLectureReview.objects.filter(lecture__platform=platform_name).delete()

    review_objs = []

    for item in final_results:
        external_id = item["id"]
        lecture = CrawledLecture.objects.get(platform=platform_name, external_id=external_id)

        for r in item.get("reviews", []):
            content = r.get("content", "").strip()
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
        CrawledLectureReview.objects.bulk_create(review_objs, batch_size=500)
        created_reviews = len(review_objs)

    return {
        "created_lectures": created_lectures,
        "updated_lectures": updated_lectures,
        "created_reviews": created_reviews,
    }
