from config.settings.base import *

# celery task test를 위한 설정입니다
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# 테스트에서 Redis broker 필요 없음
CELERY_BROKER_URL = "memory://"

# 결과 backend도 필요 없음
CELERY_RESULT_BACKEND = ""
