from typing import Optional, Tuple

from django.db import IntegrityError, transaction
from django.db.models import Q, QuerySet

from apps.recruitment.models import Tag


class TagService:

    @staticmethod
    def get_tags(keyword: str = "") -> QuerySet[Tag]:
        qs = Tag.objects.all()
        if keyword:
            qs = qs.filter(Q(name__iexact=keyword) | Q(name__icontains=keyword))
        return qs.order_by("name")

    @staticmethod
    def create_tag(name: str) -> Tuple[Optional[Tag], bool]:
        name = (name or "").strip()
        if not name:
            return None, False  # 빈값은 생성 안 함, False 반환

        try:
            with transaction.atomic():
                existing = Tag.objects.filter(name__iexact=name).first()
                if existing:
                    return existing, False
                tag = Tag.objects.create(name=name)
                return tag, True
        except IntegrityError:
            existing = Tag.objects.filter(name__iexact=name).first()
            return existing, False  # DB 제약으로 인한 경쟁 발생 시 기존 객체로 복구
