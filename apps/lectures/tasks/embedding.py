from celery import shared_task
from django.core.cache import cache
from django.db.models import QuerySet

from apps.lectures.models import CrawledLecture
from apps.lectures.services.recommendation.content_based import (
    EMBED_CACHE_TTL,
    build_lecture_embed_cache_key,
    build_lecture_embedding_vector,
)


@shared_task(  # type: ignore[misc]
    name="lectures.build_all_lecture_embeddings",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
)
def build_all_lecture_embeddings() -> int:
    lectures: QuerySet[CrawledLecture] = CrawledLecture.objects.prefetch_related("categories").all()

    count = 0
    for lecture in lectures:
        vec = build_lecture_embedding_vector(lecture)
        key = build_lecture_embed_cache_key(lecture.id)
        cache.set(key, vec.tobytes(), timeout=EMBED_CACHE_TTL)
        count += 1

    return count
