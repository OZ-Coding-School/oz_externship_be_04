from typing import Optional

from django.db.models import Count, QuerySet

from apps.study_groups.models import StudyGroup


# Admin - 스터디 그룹 가져오기
def get_admin_study_group_queryset() -> QuerySet[StudyGroup]:
    # annotate로 일괄계산된 값 적용 (N+1 이슈)
    return StudyGroup.objects.annotate(current_headcount=Count("groupmember_study_groups")).prefetch_related(
        "groupmember_study_groups__user_id",
        "studylecture_study_groups__lecture",
        # prefetch 함께 적용해 객체 반환
        "review_study_groups__user",
    )


# 그룹명 쿼리 파라미터 검색
def filter_study_groups_by_name(queryset: QuerySet[StudyGroup], search: Optional[str]) -> QuerySet[StudyGroup]:
    if search:
        queryset = queryset.filter(name__icontains=search)
    return queryset


# 스터디 상태 쿼리 파라미터 검색
def filter_study_groups_by_status(queryset: QuerySet[StudyGroup], status: Optional[str]) -> QuerySet[StudyGroup]:
    if status:
        queryset = queryset.filter(status=status)
    return queryset


# 순서 지정
def sort_study_groups(queryset: QuerySet[StudyGroup], sort: Optional[str]) -> QuerySet[StudyGroup]:
    sort_map = {
        "latest": "-created_at",
        "oldest": "created_at",
        "name_asc": "name",
        "name_desc": "-name",
    }
    order_by_field = sort_map.get(sort or "latest", sort_map["latest"])
    return queryset.order_by(order_by_field, "-id")
