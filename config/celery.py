from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

os.environ["DISABLE_GSSAPI"] = "true"  # 윈도우라서 넣었어요

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "sync_inflearn_every_midnight": {
        "task": "lectures.sync_inflearn_task",
        "schedule": crontab(hour=0, minute=0),
    },
}
