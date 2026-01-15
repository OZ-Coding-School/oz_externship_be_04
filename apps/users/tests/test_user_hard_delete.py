from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.utils import timezone

from apps.users.models import Withdrawal
from apps.users.tasks import hard_delete_user_schedule

User = get_user_model()


class UserTaskCheck(TransactionTestCase):
    def setUp(self) -> None:
        self.expired_user = User.objects.create_user(
            email="testtest@test.com", nickname="deletest", phone_number="01011110000"
        )
        Withdrawal.objects.create(
            user=self.expired_user, reason="TOO_DIFFICULT", due_date=timezone.now().date() - timedelta(days=1)
        )

        self.waiting_user = User.objects.create_user(
            email="testest@test.com", nickname="deleted", phone_number="01022220000"
        )
        Withdrawal.objects.create(
            user=self.waiting_user, reason="LACK_OF_INTEREST", due_date=timezone.now().date() + timedelta(days=1)
        )

    def test_hard_delete_task_logic(self) -> None:
        result_message = hard_delete_user_schedule()

        self.assertIn("1명의 유저가 완전 삭제됐습니다.", result_message)

        self.assertFalse(User.objects.filter(email="testtest@test.com").exists())

        self.assertTrue(User.objects.filter(email="testest@test.com").exists())

        withdrawal_record = Withdrawal.objects.get(reason="TOO_DIFFICULT")
        self.assertIsNone(withdrawal_record.user)
