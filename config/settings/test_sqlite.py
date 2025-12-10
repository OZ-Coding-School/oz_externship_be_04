from .base import *  # noqa

# SQLite를 사용해 로컬에서 가볍게 테스트한다.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_test.sqlite3",
    }
}
