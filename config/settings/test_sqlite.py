"""
SQLite용 간이 설정.
로컬에서 Swagger 등을 빠르게 확인할 때만 사용한다.
"""

import os
from pathlib import Path

# base.py 로딩 전에 필수 ENV 값을 더미로 채워 예외를 피한다.
os.environ.setdefault("DJANGO_SECRET_KEY", "dummy-secret-key")
os.environ.setdefault("DB_NAME", "dummy")
os.environ.setdefault("DB_USER", "dummy")
os.environ.setdefault("DB_PASSWORD", "dummy")
os.environ.setdefault("DB_HOST", "dummy")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("REDIS_HOST", "dummy")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "127.0.0.1 localhost")

from .base import *  # noqa: E402,F401

DEBUG = True
ALLOWED_HOSTS = ["*"]

# SQLite로 교체
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(BASE_DIR) / "db.sqlite3",
    }
}

# Redis 대신 메모리 캐시 사용
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        # pubsub_creator에서 LOCATION을 읽으므로 더미 URL을 넣어둔다.
        "LOCATION": "redis://localhost:6379/1",
    }
}

# Channels도 메모리 백엔드
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

# 개발 편의를 위한 콘솔 이메일 백엔드
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Swagger 확인 시 인증 없이도 스키마 접근 가능하도록 유지
SPECTACULAR_SETTINGS["SERVE_PERMISSIONS"] = ["rest_framework.permissions.AllowAny"]

# 정적/미디어 경로 간단 설정
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
