from collections import OrderedDict
from datetime import date
from typing import Any, Iterable, List, TypedDict

from django.db.models import Count, Max, Min
from django.db.models.functions import TruncMonth, TruncYear
from django.utils import timezone

from apps.users.models.withdrawal import Withdrawal
from apps.users.utils.admin_analytics_util import (
    DEFAULT_RECENT_MONTHS,
    DEFAULT_RECENT_YEARS,
    IntervalLiteral,
    calc_month_range,
    calc_year_range,
    init_counts_map,
)
from apps.users.utils.conts import WithdrawalReason


class WithdrawalTrendItem(TypedDict):
    """
    탈퇴 추세에서 개별 기간(월/년) 집계 데이터를 표현하는 타입
    """

    period: str
    count: int


class WithdrawalTrendResult(TypedDict):
    """
    탈퇴 추세 전체 결과를 표현하는 타입.
    """

    interval: IntervalLiteral
    from_date: date
    to_date: date
    total: int
    items: List[WithdrawalTrendItem]


def _get_monthly_withdrawal_trend(
    today: date | None = None,
    months: int = DEFAULT_RECENT_MONTHS,
) -> WithdrawalTrendResult:
    """
    최근 N개월 단위 회원탈퇴 추세를 집계
    """
    if today is None:
        today = timezone.localdate()

    start_date, end_date, labels = calc_month_range(today, months)

    qs: Iterable[dict[str, Any]] = (
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
    """
    최근 N년 단위 회원탈퇴 추세를 집계
    """

    if today is None:
        today = timezone.localdate()

    start_date, end_date, labels = calc_year_range(today, years)

    qs: Iterable[dict[str, Any]] = (
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
    """
    interval 값에 따라 월별/년별 회원탈퇴 추세를 조회합니다.
    """
    if interval == "monthly":
        return _get_monthly_withdrawal_trend()
    return _get_yearly_withdrawal_trend()


class WithdrawalReasonPercentageItem(TypedDict):
    """
    전체 기간 탈퇴 사유 비율 분석에서 개별 탈퇴 사유 한 건을 표현하는 타입
    """

    reason: str
    reason_label: str
    count: int
    percentage: float


class WithdrawalReasonPercentageResult(TypedDict):
    """
    전체 기간 탈퇴 사유 비율 분석 결과 전체를 표현하는 타입입니다.
    """

    from_date: date
    to_date: date
    total: int
    items: List[WithdrawalReasonPercentageItem]


def get_withdrawal_reason_percentage() -> WithdrawalReasonPercentageResult:
    """
    전체 기간 동안의 회원 탈퇴 사유 비율을 집계
    """

    qs_all = Withdrawal.objects.all()

    agg: dict[str, Any] = qs_all.aggregate(
        from_dt=Min("withdrawn_at"),
        to_dt=Max("withdrawn_at"),
        total=Count("id"),
    )

    total = int(agg["total"] or 0)

    if total == 0 or agg["from_dt"] is None or agg["to_dt"] is None:
        today = timezone.localdate()
        return WithdrawalReasonPercentageResult(
            from_date=today,
            to_date=today,
            total=0,
            items=[],
        )

    from_date = agg["from_dt"].date()
    to_date = agg["to_dt"].date()

    reason_counts: Iterable[dict[str, Any]] = qs_all.values("reason").annotate(count=Count("id")).order_by("-count")

    items: List[WithdrawalReasonPercentageItem] = []

    for row in reason_counts:
        reason_value: str = row["reason"]
        count: int = int(row["count"])
        percentage = round(count / total * 100, 2) if total > 0 else 0.0

        try:
            reason_choice = WithdrawalReason(reason_value)
            reason_label = str(reason_choice.label)
        except ValueError:
            reason_label = reason_value

        items.append(
            WithdrawalReasonPercentageItem(
                reason=reason_value,
                reason_label=reason_label,
                count=count,
                percentage=percentage,
            )
        )

    return WithdrawalReasonPercentageResult(
        from_date=from_date,
        to_date=to_date,
        total=total,
        items=items,
    )


class WithdrawalReasonMonthlyStatsItem(TypedDict):
    """
    월별 탈퇴 사유 분석에서 개별 월별 데이터를 표현하는 타입
    """

    period: str
    count: int


class WithdrawalReasonMonthlyStatsResult(TypedDict):
    """
    월별 탈퇴 사유 분석 결과 전체를 표현하는 타입
    """

    reason: str
    reason_label: str
    from_date: date
    to_date: date
    total: int
    items: List[WithdrawalReasonMonthlyStatsItem]


def get_withdrawal_reason_monthly_stats(
    reason: str,
    today: date | None = None,
    months: int = DEFAULT_RECENT_MONTHS,
) -> WithdrawalReasonMonthlyStatsResult:
    """
    특정 탈퇴 사유(reason)에 대해, 최근 N개월 동안의 월별 탈퇴 추세를 집계
    """

    if today is None:
        today = timezone.localdate()

    start_date, end_date, labels = calc_month_range(today, months)

    qs: Iterable[dict[str, Any]] = (
        Withdrawal.objects.filter(
            reason=reason,
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

    items: List[WithdrawalReasonMonthlyStatsItem] = [
        WithdrawalReasonMonthlyStatsItem(period=label, count=count) for label, count in counts_map.items()
    ]
    total = sum(counts_map.values())

    try:
        reason_choice = WithdrawalReason(reason)
        reason_label = str(reason_choice.label)
    except ValueError:
        reason_label = reason

    return WithdrawalReasonMonthlyStatsResult(
        reason=reason,
        reason_label=reason_label,
        from_date=start_date,
        to_date=end_date,
        total=total,
        items=items,
    )
