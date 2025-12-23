from collections import OrderedDict
from datetime import date, timedelta
from typing import List, Literal

IntervalLiteral = Literal["monthly", "yearly"]

DEFAULT_RECENT_MONTHS: int = 12
DEFAULT_RECENT_YEARS: int = 5


def calc_month_range(today: date, months: int) -> tuple[date, date, List[str]]:
    base = today.replace(day=1)
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


def calc_year_range(today: date, years: int) -> tuple[date, date, List[str]]:

    current_year = today.year
    start_year = current_year - (years - 1)

    start_date = date(start_year, 1, 1)
    end_date = date(current_year, 12, 31)

    labels: List[str] = [f"{year}" for year in range(start_year, current_year + 1)]

    return start_date, end_date, labels


def init_counts_map(labels: List[str]) -> "OrderedDict[str, int]":

    return OrderedDict((label, 0) for label in labels)
