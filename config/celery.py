from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
os.environ["DISABLE_GSSAPI"] = "true"

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.TASK_ALWAYS_EAGER = True
app.conf.task_eager_propagates = True

app.autodiscover_tasks()

app.conf.timezone = "Asia/Seoul"

app.conf.beat_schedule = {
    "sync_inflearn_every_midnight": {
        "task": "lectures.sync_inflearn_task",
        "schedule": crontab(hour=0, minute=0),
    },
    "send_tomorrow_schedule_notifications": {
        "task": "apps.notification.infra.task.send_tomorrow_schedule_notifications",
        "schedule": crontab(hour=0, minute=1),
    },
    "send_today_schedule_notifications": {
        "task": "apps.notification.infra.task.send_today_schedule_notifications",
        "schedule": crontab(hour=0, minute=1),
    },
}
