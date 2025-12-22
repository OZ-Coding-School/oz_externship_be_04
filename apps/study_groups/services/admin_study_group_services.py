from typing import Optional

from django.db.models import QuerySet

from apps.study_groups.models import StudyGroup


# Admin - 스터디 그룹 가져오기
def get_admin_study_group_queryset() -> QuerySet[StudyGroup]:
    return StudyGroup.objects.prefetch_related(
        "groupmember_study_groups__user_id",
        "studylecture_study_groups__lecture",
        "review_study_groups",
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
