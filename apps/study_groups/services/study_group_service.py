from typing import Any, Optional

from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from apps.study_groups.models import GroupMember, StudyGroup
from apps.users.models import User as CustomUser


# 스터디 그룹 생성
def create_study_group(user: CustomUser, validated_data: dict[str, Any]) -> StudyGroup:
    lectures = validated_data.pop("lectures", [])
    study_group = StudyGroup.objects.create(**validated_data)
    GroupMember.objects.create(study_group_id=study_group, user_id=user, is_leader=True)
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
def retrieve_study_group(group_id: int) -> StudyGroup:
    return get_object_or_404(
        StudyGroup.objects.prefetch_related(
            # prefetch 객체(강의/유저) 추가
            "studylecture_study_groups__lecture",
            "groupmember_study_groups__user_id",
        ),
        pk=group_id,
    )


# 스터디 그룹 수정
def update_study_group(study_group: StudyGroup, validated_data: dict[str, str]) -> StudyGroup:
    for attr, value in validated_data.items():
        setattr(study_group, attr, value)
    study_group.save()
    return study_group


# 스터디 그룹 삭제
def delete_study_group(study_group: StudyGroup, user: CustomUser) -> None:
    leader = GroupMember.objects.filter(
        study_group_id=study_group.id,
        user_id=user.id,
        is_leader=True,
    ).first()

    if leader is None:
        raise PermissionError("스터디 그룹 삭제 권한이 없습니다.")

    study_group.delete()


# 리더 위임
# 전체 트랙젝션 시 @transaction.atomic 데코레이터 형태로도 사용가능
def delegate_leader(*, group_id: int, current_user: CustomUser, target_user_id: int) -> None:
    with transaction.atomic():
        current_leader = (
            GroupMember.objects.select_for_update()
            .filter(
                study_group_id=group_id,
                user_id=current_user.id,
                is_leader=True,
            )
            .first()
        )

        if current_leader is None:
            raise PermissionError("리더만 권한을 위임할 수 있습니다.")

        target_member = (
            GroupMember.objects.select_for_update()
            .filter(
                study_group_id=group_id,
                user_id=target_user_id,
            )
            .first()
        )

        if target_member is None:
            raise ValueError("해당 멤버를 찾을 수 없습니다.")

        if target_member.is_leader:
            raise ValueError("이미 리더인 멤버입니다.")

        current_leader.is_leader = False
        current_leader.save(update_fields=["is_leader"])

        target_member.is_leader = True
        target_member.save(update_fields=["is_leader"])


# 스터디 그룹 나가기
def leave_study_group(*, group_id: int, user: CustomUser) -> None:
    membership = GroupMember.objects.filter(
        study_group_id=group_id,
        user_id=user.id,
    ).first()

    if membership is None:
        raise ValueError("스터디 그룹에 속해있지 않습니다.")

    if membership.is_leader:
        raise ValueError("리더는 스터디 그룹을 나갈 수 없습니다.")

    membership.delete()


# 멤버 추방
def kick_member(*, group_id: int, current_user: CustomUser, target_user_id: int) -> None:
    current_leader = GroupMember.objects.filter(
        study_group_id=group_id,
        user_id=current_user.id,
        is_leader=True,
    ).first()

    if current_leader is None:
        raise PermissionError("리더만 멤버를 추방할 수 있습니다.")

    target_member = GroupMember.objects.filter(
        study_group_id=group_id,
        user_id=target_user_id,
    ).first()

    if target_member is None:
        raise ValueError("해당 멤버를 찾을 수 없습니다.")

    if target_member.is_leader:
        raise ValueError("리더는 추방할 수 없습니다.")

    target_member.delete()
