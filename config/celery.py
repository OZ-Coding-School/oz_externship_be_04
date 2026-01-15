from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab

os.environ["DISABLE_GSSAPI"] = "true"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.timezone = "Asia/Seoul"

app.conf.beat_schedule = {
    "crawl_and_embed_every_midnight": {
        "task": "lectures.crawl_then_embed",
        "schedule": crontab(hour=0, minute=0),
    },
    "send_tomorrow_schedule_notifications": {
        "task": "send_tomorrow_schedule_notifications",
        "schedule": crontab(hour=0, minute=1),
    },
    "send_today_schedule_notifications": {
        "task": "send_today_schedule_notifications",
        "schedule": crontab(hour=0, minute=1),
    },
    "hard_delete_expired_users": {
        "task": "apps.users.tasks.hard_delete_user_schedule",
        "schedule": crontab(hour=0, minute=0),
    },
}
