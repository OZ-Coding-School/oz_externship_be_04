from collections import OrderedDict
from datetime import date
from typing import Any, List, TypedDict

from django.db.models import Count, QuerySet
from django.db.models.functions import TruncMonth, TruncYear
from django.utils import timezone

from apps.users.models.withdrawal import Withdrawal
from apps.users.services.admin_analytics_common import (
    DEFAULT_RECENT_MONTHS,
    DEFAULT_RECENT_YEARS,
    IntervalLiteral,
    calc_month_range,
    calc_year_range,
    init_counts_map,
)


class WithdrawalTrendItem(TypedDict):
    period: str
    count: int


class WithdrawalTrendResult(TypedDict):
    interval: IntervalLiteral
    from_date: date
    to_date: date
    total: int
    items: List[WithdrawalTrendItem]


def _get_monthly_withdrawal_trend(
    today: date | None = None,
    months: int = DEFAULT_RECENT_MONTHS,
) -> WithdrawalTrendResult:
    if today is None:
        today = timezone.localdate()

    start_date, end_date, labels = calc_month_range(today, months)

    qs: QuerySet[Any] = (
        Withdrawal.objects.filter(
            withdrawn_at__date__gte=start_date,
            withdrawn_at__date__lte=end_date,
        )
        .annotate(period=TruncMonth("withdrawn_at"))
        .values("period")
        .annotate(count=Count("id"))
        .order_by("period")
    )

    counts_map: "OrderedDict[str, int]" = init_counts_map(labels)

    for row in qs:
        period_date = row["period"]
        label = f"{period_date.year:04d}-{period_date.month:02d}"
        if label in counts_map:
            counts_map[label] = int(row["count"])

    items: List[WithdrawalTrendItem] = [
        WithdrawalTrendItem(period=label, count=count) for label, count in counts_map.items()
    ]
    total = sum(counts_map.values())

    return WithdrawalTrendResult(
        interval="monthly",
        from_date=start_date,
        to_date=end_date,
        total=total,
        items=items,
    )


def _get_yearly_withdrawal_trend(
    today: date | None = None,
    years: int = DEFAULT_RECENT_YEARS,
) -> WithdrawalTrendResult:

    if today is None:
        today = timezone.localdate()

    start_date, end_date, labels = calc_year_range(today, years)

    qs: QuerySet[Any] = (
        Withdrawal.objects.filter(
            withdrawn_at__date__gte=start_date,
            withdrawn_at__date__lte=end_date,
        )
        .annotate(period=TruncYear("withdrawn_at"))
        .values("period")
        .annotate(count=Count("id"))
        .order_by("period")
    )

    counts_map: "OrderedDict[str, int]" = init_counts_map(labels)

    for row in qs:
        period_date = row["period"]
        label = f"{period_date.year}"
        if label in counts_map:
            counts_map[label] = int(row["count"])

    items: List[WithdrawalTrendItem] = [
        WithdrawalTrendItem(period=label, count=count) for label, count in counts_map.items()
    ]
    total = sum(counts_map.values())

    return WithdrawalTrendResult(
        interval="yearly",
        from_date=start_date,
        to_date=end_date,
        total=total,
        items=items,
    )


def get_withdrawal_trend(interval: IntervalLiteral) -> WithdrawalTrendResult:

    if interval == "monthly":
        return _get_monthly_withdrawal_trend()
    return _get_yearly_withdrawal_trend()
