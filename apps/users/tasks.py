from celery import shared_task
from django.utils import timezone

from apps.users.models import Withdrawal


@shared_task  # type: ignore
def hard_delete_user_schedule() -> str:
    today = timezone.now().date()
    check_expired_users = Withdrawal.objects.filter(
        due_date__lte=today,
        user__isnull=False,
    )

    count: int = 0
    for withdrawal in check_expired_users:
        if withdrawal.user:
            withdrawal.user.delete()
            count += 1
    return f"{count}명의 유저가 완전 삭제됐습니다."
