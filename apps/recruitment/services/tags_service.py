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
            return None, False
        existing = Tag.objects.filter(name__iexact=name).first()
        if existing:
            return existing, False

        tag = Tag.objects.create(name=name)
        return tag, True
