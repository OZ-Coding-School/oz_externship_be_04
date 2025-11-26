from apps.lectures.models.category import Category, LectureCategory, UserPreferCategory
from apps.lectures.models.crawled_lecture import CrawledLecture
from apps.lectures.models.crawled_lecture_review import CrawledLectureReview
from apps.lectures.models.lecture_bookmark import LectureBookmark
__all__ = [
    "CrawledLecture",
    "CrawledLectureReview",
    "Category",
    "LectureCategory",
    "UserPreferCategory",
]
