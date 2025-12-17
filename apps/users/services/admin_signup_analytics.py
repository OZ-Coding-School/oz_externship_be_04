from __future__ import annotations

from collections import OrderedDict
from datetime import date, timedelta
from typing import List, Literal, TypedDict

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncYear
from django.utils import timezone

User = get_user_model()

IntervalLiteral = Literal["monthly", "yearly"]

DEFAULT_RECENT_MONTHS: int = 12
DEFAULT_RECENT_YEARS: int = 5


class SignupTrendItem(TypedDict):
    period: str
    count: int


class SignupTrendResult(TypedDict):
    interval: IntervalLiteral
    from_date: date
    to_date: date
    total: int
    items: List[SignupTrendItem]


def _month_range_base(today: date) -> date:
    """
    오늘 날짜 기준으로 해당 달의 1일을 반환합니다.
    """
    return today.replace(day=1)


def _calc_month_range(today: date, months: int) -> tuple[date, date, List[str]]:
    base = _month_range_base(today)
    year = base.year
    month = base.month - (months - 1)

    while month <= 0:
        month += 12
        year -= 1

    start_date = date(year, month, 1)

    if base.month == 12:
        next_month_first = date(base.year + 1, 1, 1)
    else:
        next_month_first = date(base.year, base.month + 1, 1)

    end_date = next_month_first - timedelta(days=1)

    labels: List[str] = []
    cur_year, cur_month = year, month
    for _ in range(months):
        labels.append(f"{cur_year:04d}-{cur_month:02d}")
        cur_month += 1
        if cur_month > 12:
            cur_month = 1
            cur_year += 1

    return start_date, end_date, labels


def _get_monthly_signup_trend(
    today: date | None = None,
    months: int = DEFAULT_RECENT_MONTHS,
) -> SignupTrendResult:
    if today is None:
        today = timezone.localdate()

    start_date, end_date, labels = _calc_month_range(today, months)

    qs = (
        User.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        .annotate(period=TruncMonth("created_at"))
        .values("period")
        .annotate(count=Count("id"))
        .order_by("period")
    )

    counts_map: "OrderedDict[str, int]" = OrderedDict((label, 0) for label in labels)

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
    if today is None:
        today = timezone.localdate()

    current_year = today.year
    start_year = current_year - (years - 1)

    start_date = date(start_year, 1, 1)
    end_date = date(current_year, 12, 31)

    qs = (
        User.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        .annotate(period=TruncYear("created_at"))
        .values("period")
        .annotate(count=Count("id"))
        .order_by("period")
    )

    labels: List[str] = [f"{year}" for year in range(start_year, current_year + 1)]
    counts_map: "OrderedDict[str, int]" = OrderedDict((label, 0) for label in labels)

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
    if interval == "monthly":
        return _get_monthly_signup_trend()
    return _get_yearly_signup_trend()
