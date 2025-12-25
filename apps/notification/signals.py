from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.application.models import Application, ApplicationStatus
from apps.notification.infra.task import send_to_pubsub
from apps.notification.models import Notification
from apps.study_groups.models import GroupMember, StudyGroup, StudyNote


@receiver(post_save, sender=Application)
def recruitment_created(sender: Any, instance: Application, created: bool, **kwargs: Any) -> None:
    """공고 지원 알림"""
    if not created:
        return

    recruitment = instance.recruitment
    recruitment_uuid = recruitment.uuid
    back_url = f"https://learn.ozcoding.site/manage?recruitment_uuid={recruitment_uuid}"

    notification = Notification.objects.create(
        user=recruitment.author,
        content=f"공고:'{recruitment.title}'에 새로운 지원자가 지원했습니다.",
        type=Notification.NotificationType.ADD_APPLICATION,
        back_url_link=back_url,
    )

    send_to_pubsub.delay(notification.id)


@receiver(post_save, sender=Application)
def recruitment_approved_rejected_created(sender: Any, instance: Application, created: bool, **kwargs: Any) -> None:
    """공고 지원 승인 및 거절 알림"""
    if not created and instance.status in [ApplicationStatus.ACCEPTED, ApplicationStatus.REJECTED]:
        recruitment = instance.recruitment
        recruitment_id = recruitment.id

        back_url = f"https://account.ozcoding.site/mypage?state=APPLY_LIST&recruitment_id={recruitment_id}"

        if instance.status == ApplicationStatus.ACCEPTED:
            notification = Notification.objects.create(
                user=instance.applicant,
                content=f"'{recruitment.title}'구인 공고에 대한 지원내역이 승인되었습니다.",
                type=Notification.NotificationType.APPLICATION_ACCEPT,
                back_url_link=back_url,
            )
        else:
            notification = Notification.objects.create(
                user=instance.applicant,
                content=f"'{recruitment.title}'구인 공고에 대한 지원내역이 거절되었습니다.",
                type=Notification.NotificationType.APPLICATION_REJECT,
                back_url_link=back_url,
            )
        send_to_pubsub.delay(notification.id)


@receiver(post_save, sender=Application)
def study_member_joined_created(sender: Any, instance: Application, created: bool, **kwargs: Any) -> None:
    """스터디 그룹 참여 알림"""
    if not created and instance.status == ApplicationStatus.ACCEPTED:
        recruitment = instance.recruitment

        if recruitment.study_group:
            study_group = recruitment.study_group
            new_member = instance.applicant

            study_group_id = study_group.id
            back_url = f"study_group_id : {study_group_id}"

            existing_studymember = GroupMember.objects.filter(study_group_id=study_group.id).exclude(
                user_id=new_member.id
            )

            notifications = [
                Notification(
                    user_id=member.user_id.id,
                    content=f"{study_group.name}에 {new_member.nickname}님이 참여했습니다. 환영해주세요!",
                    type=Notification.NotificationType.STUDY_JOIN,
                    back_url_link=back_url,
                )
                for member in existing_studymember
            ]

            created_notifications = Notification.objects.bulk_create(notifications)

            for notification in created_notifications:
                send_to_pubsub.delay(notification.id)


@receiver(post_save, sender=StudyGroup)
def study_review_request_created(sender: Any, instance: StudyGroup, created: bool, **kwargs: Any) -> None:
    """스터디 그룹 후기 작성 요청 알림"""
    if not created and instance.status == StudyGroup.StudyGroupStatusChoices.ENDED:
        group_members = GroupMember.objects.filter(study_group_id=instance)

        study_group_id = instance.id
        back_url = f"https://study.ozcoding.site/{study_group_id}"

        notifications = [
            Notification(
                user_id=member.user_id.id,
                content=f"오늘은 {instance.name}의 종료일이에요! 스터디 후기를 기록해주세요!",
                type=Notification.NotificationType.STUDY_REVIEW_REQUEST,
                back_url_link=back_url,
            )
            for member in group_members
        ]

        created_notifications = Notification.objects.bulk_create(notifications)

        for notification in created_notifications:
            send_to_pubsub.delay(notification.id)


@receiver(post_save, sender=StudyNote)
def study_record_request_created(sender: Any, instance: StudyNote, created: bool, **kwargs: Any) -> None:
    """스터디 기록 작성 알림"""
    if not created:
        return

    study_group = instance.study_group
    author = instance.author

    if study_group and author:
        study_group_id = study_group.id
        study_note_id = instance.id
        back_url = f"https://study.ozcoding.site/{study_group_id}/notes/{study_note_id}"
        existing_member = GroupMember.objects.filter(study_group_id=study_group.id).exclude(user_id=author.id)

        notifications = [
            Notification(
                user_id=member.user_id.id,
                content=f"{author.nickname}님이 {study_group.name}에 스터디 기록을 작성하셨습니다. 확인해보세요!",
                type=Notification.NotificationType.STUDY_NOTE_CREATE,
                back_url_link=back_url,
            )
            for member in existing_member
        ]

        created_notifications = Notification.objects.bulk_create(notifications)

        for notification in created_notifications:
            send_to_pubsub.delay(notification.id)
