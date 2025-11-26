from apps.lectures.models.category import Category
from apps.lectures.models.crawled_lecture import CrawledLecture
from apps.lectures.models.crawled_lecture_review import CrawledLectureReview
from apps.lectures.models.lecture_category import LectureCategory
from apps.lectures.models.user_prefer_category import UserPreferCategory

__all__ = [
    "CrawledLecture",
    "CrawledLectureReview",
    "Category",
    "LectureCategory",
    "UserPreferCategory",
]
