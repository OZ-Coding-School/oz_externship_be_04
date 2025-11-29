from dataclasses import dataclass, field
from math import ceil
from typing import Generic, List, Sequence, TypeVar

from django.db.models import Model, QuerySet

T = TypeVar("T", bound=Model)


@dataclass(frozen=True)
class Pageable:
    page: int = 1
    size: int = 10

    def __post_init__(self) -> None:
        normalized_page = max(1, self.page)
        normalized_size = max(1, self.size)
        object.__setattr__(self, "page", normalized_page)
        object.__setattr__(self, "size", normalized_size)

    @classmethod
    def from_params(cls, page_raw: str | None, size_raw: str | None) -> "Pageable":

        def parse_int(raw: str | None, default: int) -> int:
            if raw is None:
                return default
            try:
                return int(raw)
            except ValueError:
                return default

        page = parse_int(page_raw, 1)
        size = parse_int(size_raw, 10)
        return cls(page=page, size=size)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


@dataclass
class OffsetPage(Generic[T]):
    items: List[T]
    current_page: int
    size: int
    total_count: int
    total_pages: int = field(init=False)
    has_next: bool = field(init=False)
    has_prev: bool = field(init=False)

    def __post_init__(self) -> None:
        if self.size <= 0:
            self.total_pages = 0
        else:
            self.total_pages = int(ceil(self.total_count / self.size))
        self.has_next = self.current_page < self.total_pages
        self.has_prev = self.current_page > 1


def offset_paginate_queryset(
    queryset: QuerySet[T],
    pageable: Pageable,
) -> OffsetPage[T]:
    total_count: int = queryset.count()
    start = pageable.offset
    end = start + pageable.limit
    items: List[T] = list(queryset[start:end])
    return OffsetPage(
        items=items,
        current_page=pageable.page,
        size=pageable.size,
        total_count=total_count,
    )


def offset_paginate_list(
    items: Sequence[T],
    pageable: Pageable,
) -> OffsetPage[T]:
    total_count: int = len(items)
    start = pageable.offset
    end = start + pageable.limit
    page_items: List[T] = list(items[start:end])
    return OffsetPage(
        items=page_items,
        current_page=pageable.page,
        size=pageable.size,
        total_count=total_count,
    )
