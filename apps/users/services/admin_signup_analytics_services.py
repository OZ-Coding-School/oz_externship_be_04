from __future__ import annotations

from datetime import date
from typing import List, TypedDict

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncYear
from django.utils import timezone

from apps.users.utils.admin_analytics_util import (
    DEFAULT_RECENT_MONTHS,
    DEFAULT_RECENT_YEARS,
    IntervalLiteral,
    calc_month_range,
    calc_year_range,
    init_counts_map,
)

User = get_user_model()


class SignupTrendItem(TypedDict):
    """
    회원가입 추세에서 개별 기간(월/년) 별 집계 데이터를 표현하는 타입
    """

    period: str
    count: int


class SignupTrendResult(TypedDict):
    """
    회원가입 추세 전체 결과를 표현하는 타입입니다.
    """

    interval: IntervalLiteral
    from_date: date
    to_date: date
    total: int
    items: List[SignupTrendItem]


def _get_monthly_signup_trend(
    today: date | None = None,
    months: int = DEFAULT_RECENT_MONTHS,
) -> SignupTrendResult:
    """
    최근 N개월 단위 회원가입 추세를 집계
    """
    if today is None:
        today = timezone.localdate()

    start_date, end_date, labels = calc_month_range(today, months)

    qs = (
        User.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        .annotate(period=TruncMonth("created_at"))
        .values("period")
        .annotate(count=Count("id"))
        .order_by("period")
    )

    counts_map = init_counts_map(labels)

    for row in qs:
        period_date = row["period"]
        label = f"{period_date.year:04d}-{period_date.month:02d}"
        if label in counts_map:
            counts_map[label] = int(row["count"])

    items: List[SignupTrendItem] = [SignupTrendItem(period=label, count=count) for label, count in counts_map.items()]
    total = sum(counts_map.values())

    return SignupTrendResult(
        interval="monthly",
        from_date=start_date,
        to_date=end_date,
        total=total,
        items=items,
    )


def _get_yearly_signup_trend(
    today: date | None = None,
    years: int = DEFAULT_RECENT_YEARS,
) -> SignupTrendResult:
    """
    최근 N년 단위 회원가입 추세를 집계
    """

    if today is None:
        today = timezone.localdate()

    start_date, end_date, labels = calc_year_range(today, years)

    qs = (
        User.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        .annotate(period=TruncYear("created_at"))
        .values("period")
        .annotate(count=Count("id"))
        .order_by("period")
    )

    counts_map = init_counts_map(labels)

    for row in qs:
        period_date = row["period"]
        label = f"{period_date.year}"
        if label in counts_map:
            counts_map[label] = int(row["count"])

    items: List[SignupTrendItem] = [SignupTrendItem(period=label, count=count) for label, count in counts_map.items()]
    total = sum(counts_map.values())

    return SignupTrendResult(
        interval="yearly",
        from_date=start_date,
        to_date=end_date,
        total=total,
        items=items,
    )


def get_signup_trend(interval: IntervalLiteral) -> SignupTrendResult:
    """
    interval 값에 따라 월별/년별 회원가입 추세를 조회
    """

    if interval == "monthly":
        return _get_monthly_signup_trend()
    return _get_yearly_signup_trend()
