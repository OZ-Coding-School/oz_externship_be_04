import logging
from typing import Any, Optional

from celery import shared_task
from django.db import transaction
from django.db.models import Count, QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.study_groups.models import GroupMember, StudyGroup, StudyLecture
from apps.users.models import User as CustomUser

logger = logging.getLogger(__name__)


# 스터디 그룹 생성
def create_study_group(user: CustomUser, validated_data: dict[str, Any]) -> StudyGroup:
    lectures_data = validated_data.pop("lectures", [])

    # 오늘 날짜와 request 날짜 비교하여 status 자동 설정 로직
    today = timezone.now()
    start_at = validated_data.get("start_at")
    end_at = validated_data.get("end_at")

    if start_at and end_at:
        # end_at 다음날부터 ENDED 처리 (end_at 당일까지는 ONGOING)
        if end_at < today:
            validated_data["status"] = StudyGroup.StudyGroupStatusChoices.ENDED
        elif start_at <= today:
            validated_data["status"] = StudyGroup.StudyGroupStatusChoices.ONGOING
        else:
            validated_data["status"] = StudyGroup.StudyGroupStatusChoices.PENDING

    study_group = StudyGroup.objects.create(**validated_data)

    # 강의 저장 (StudyLecture 생성)
    if lectures_data:
        lectures = [
            StudyLecture(
                study_group=study_group,
                lecture_id=lecture_id,
            )
            for lecture_id in lectures_data
        ]
        StudyLecture.objects.bulk_create(lectures)

    GroupMember.objects.create(study_group_id=study_group, user_id=user, is_leader=True)
    return study_group


# 스터디 그룹 목록 조회


def get_study_group_list(user: CustomUser, status: Optional[str] = None) -> QuerySet[StudyGroup]:
    # 소속 그룹만 필터링
    user_group_ids = GroupMember.objects.filter(user_id=user.id).values_list("study_group_id", flat=True)
    queryset = (  # annotate 사용해 N+1 이슈 해결 (쿼리 반복 감소)
        StudyGroup.objects.filter(id__in=user_group_ids)
        .annotate(current_headcount=Count("groupmember_study_groups"))
        .prefetch_related(
            "studylecture_study_groups__lecture",
            "groupmember_study_groups__user_id",
            "review_study_groups__user",
        )
    )
    if status:
        queryset = queryset.filter(status=status)
    return queryset


# 스터디 그룹 상세 조회
def retrieve_study_group(group_id: int, user: CustomUser) -> StudyGroup:
    # 소속 그룹만 필터링 / 오류 404 처리
    study_group = get_object_or_404(
        # annotate로 DB에서 계산하여 객체에 필드 추가 (쿼리 반복 N+1 이슈 해결)
        StudyGroup.objects.annotate(current_headcount=Count("groupmember_study_groups")).prefetch_related(
            "studylecture_study_groups__lecture",
            "groupmember_study_groups__user_id",
        ),
        pk=group_id,
    )

    # 소속 멤버 여부 검증 / 404 처리
    is_member = GroupMember.objects.filter(
        study_group_id=study_group.id,
        user_id=user.id,
    ).exists()

    if not is_member:
        raise Http404("소속된 스터디 그룹이 아닙니다.")

    return study_group


# 스터디 그룹 수정 (강의 모델 실제 구조에 맞추어 str,any로 타입 수정)
def update_study_group(study_group: StudyGroup, validated_data: dict[str, Any]) -> StudyGroup:
    lectures_data = validated_data.pop("lectures", None)

    for attr, value in validated_data.items():
        setattr(study_group, attr, value)
    study_group.save()

    # 강의 상태 수정
    if lectures_data is not None:
        with transaction.atomic():
            StudyLecture.objects.filter(study_group=study_group).delete()
            if lectures_data:
                lectures = [
                    StudyLecture(
                        study_group=study_group,
                        lecture_id=lecture_id,
                    )
                    for lecture_id in lectures_data
                ]
                StudyLecture.objects.bulk_create(lectures)

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


# 스터디 그룹 상태 자동 갱신 (celery beat 사용해 작업 예약)
@shared_task(name="study_groups.update_study_group_statuses")  # type: ignore[misc]
def update_all_study_group_statuses() -> dict[str, int]:
    try:
        today = timezone.now()
        updated_count = 0

        # PENDING → ONGOING
        pending_to_ongoing = StudyGroup.objects.filter(
            status=StudyGroup.StudyGroupStatusChoices.PENDING,
            start_at__lte=today,
        )
        for study_group in pending_to_ongoing:
            if study_group.status == StudyGroup.StudyGroupStatusChoices.PENDING:
                study_group.status = StudyGroup.StudyGroupStatusChoices.ONGOING
                study_group.save(update_fields=["status"])
                updated_count += 1

        # ONGOING → ENDED (end_at 다음날부터 ENDED 처리)
        ongoing_to_ended = StudyGroup.objects.filter(
            status=StudyGroup.StudyGroupStatusChoices.ONGOING,
            end_at__lt=today,
        )
        for study_group in ongoing_to_ended:
            if study_group.status == StudyGroup.StudyGroupStatusChoices.ONGOING:
                study_group.status = StudyGroup.StudyGroupStatusChoices.ENDED
                study_group.save(update_fields=["status"])
                updated_count += 1

        result = {"updated_count": updated_count}
        logger.info(f"스터디 그룹 상태 갱신 완료: {result['updated_count']}개 그룹이 갱신되었습니다.")
        return result
    except Exception as e:
        logger.exception(f"스터디 그룹 상태 갱신 중 오류 발생: {e}")
        raise
