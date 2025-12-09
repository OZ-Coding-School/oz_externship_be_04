from apps.lectures.urls.crawled_lecture_url import urlpatterns as crawled_urlpatterns
from apps.lectures.urls.lecture_bookmark_url import urlpatterns as bookmark_urlpatterns

urlpatterns = [
    *crawled_urlpatterns,
    *bookmark_urlpatterns,
]
