# from typing import Optional
#
# from apps.notification.models.notification import Notification
# from apps.users.models import User
#
#
# # 외부에서 호출하는 단 하나의 함수
# def send_notification(user: User, type: Notification.NotificationType, content: str, back_url_link: Optional[str] = None) -> Notification:
#     pass


# return Notification.objects.create(  # type: ignore
#     user=user, type=type.value, content=content, back_url_link=back_url_link or ""
# )


# type 목록
# STUDY_JOIN = "STUDY_JOIN", "스터디 그룹에 새로운 구성원이 참가한 경우 알림"
# STUDY_NOTE_CREATE = "STUDY_NOTE_CREATE", "스터디 구성원이 스터디 기록을 작성한 경우 알림"
# STUDY_REVIEW_REQUEST = "STUDY_REVIEW_REQUEST", "스터디 종료가 도래한 경우 알림"
# APPLICATION_ACCEPT = "APPLICATION_ACCEPT", "지원내역이 승인된 경우 알림"
# APPLICATION_REJECT = "APPLICATION_REJECT", "지원내역이 거절된 경우 알림"
# ADD_APPLICATION = "ADD_APPLICATION", "공고를 올린 스터디 그룹의 리더에게 새로운 지원내역이 있는 경우 알림"
# TODAY_SCHEDULE = "TODAY_SCHEDULE", "금일 스케줄 알림"
# UPCOMING_SCHEDULE = "UPCOMING_SCHEDULE", "스케줄 하루 전에 임박한 예정 스케줄 알림"
