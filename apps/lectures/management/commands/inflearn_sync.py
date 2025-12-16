from typing import Any

from django.core.management.base import BaseCommand

from apps.lectures.services.inflearn_sync_service import run_inflearn_sync


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        result = run_inflearn_sync()
        self.stdout.write(self.style.SUCCESS(f"동기화 완료: {result}개"))
