from typing import Optional, Tuple

from django.db.models import Q, QuerySet

from apps.recruitment.models import Tag


class TagService:

    @staticmethod
    def get_tags(keyword: str = "") -> QuerySet[Tag]:
        qs = Tag.objects.all()
        if keyword:
            qs = qs.filter(Q(name__iexact=keyword) | Q(name__icontains=keyword))
        return qs.order_by("name")
