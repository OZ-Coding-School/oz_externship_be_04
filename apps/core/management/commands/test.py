from typing import Any

import redis.client
from django.conf import settings
from django.core.management.commands.test import Command as TestCommand


class Command(TestCommand):
    def handle(self, *test_labels: Any, **options: Any) -> None:
        self.teardown_redis()
        super().handle(*test_labels, **options)
        self.teardown_redis()

    @staticmethod
    def teardown_redis() -> None:
        try:
            redis.client.Redis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/15").flushdb()
        except Exception:
            # 로컬 테스트에서 레디스가 없어도 넘어가게 한다.
            pass
