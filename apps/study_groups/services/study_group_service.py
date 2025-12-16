from typing import Any, Optional

from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from apps.study_groups.models import GroupMember, StudyGroup, StudyLecture
from apps.users.models import User as CustomUser


# 스터디 그룹 생성
def create_study_group(user: CustomUser, validated_data: dict[str, Any]) -> StudyGroup:
    lectures = validated_data.pop("lectures", [])
    study_group = StudyGroup.objects.create(**validated_data)
    GroupMember.objects.create(study_group_id=study_group, user_id=user, is_leader=True)
    if lectures:
        StudyLecture.objects.bulk_create(
            [
                StudyLecture(
                    study_group_id=study_group.id,
                    lecture_id=lecture_id,
                )
                for lecture_id in lectures
            ]
        )
    return study_group


# 스터디 그룹 목록 조회
def get_study_group_list(status: Optional[str] = None) -> QuerySet[StudyGroup]:  # list -> 쿼리셋으로 수정
    queryset = StudyGroup.objects.prefetch_related(
        "studylecture_study_groups", "groupmember_study_groups", "review_study_groups"
    )
    if status:
        queryset = queryset.filter(status=status)
    return queryset


# 스터디 그룹 상세 조회
def retrieve_study_group(pk: int) -> StudyGroup:
    return get_object_or_404(
        StudyGroup.objects.prefetch_related(
            "studylecture_study_groups",
            "groupmember_study_groups",
        ),
        pk=pk,
    )


# 스터디 그룹 수정
def update_study_group(study_group: StudyGroup, validated_data: dict[str, str]) -> StudyGroup:
    for attr, value in validated_data.items():
        setattr(study_group, attr, value)
    study_group.save()
    return study_group


# 스터디 그룹 삭제
def delete_study_group(study_group: StudyGroup) -> None:
    study_group.delete()


# 리더 위임
# 전체 트랙젝션 시 @transaction.atomic 데코레이터 형태로도 사용가능
def delegate_leader(current_leader: GroupMember, target_member: GroupMember) -> None:

    with transaction.atomic():
        current_leader.is_leader = False
        current_leader.save(update_fields=["is_leader"])

        target_member.is_leader = True
        target_member.save(update_fields=["is_leader"])


# 스터디 그룹 나가기
def leave_study_group(member: GroupMember) -> None:
    if member.is_leader:
        raise ValueError("리더는 스터디 그룹을 나갈 수 없습니다.")
    member.delete()


# 멤버 추방
def kick_member(current_leader: GroupMember, target_member: GroupMember) -> None:
    if not current_leader.is_leader:
        raise PermissionError("리더만 멤버를 추방할 수 있습니다.")
    if target_member.is_leader:
        raise ValueError("리더는 추방할 수 없습니다.")
    target_member.delete()
