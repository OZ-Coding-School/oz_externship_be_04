from apps.study_groups.models.group_member import GroupMember
from apps.study_groups.models.study_group import StudyGroup
from apps.study_groups.models.syudy_lecture import StudyLecture

# 프로젝트 절대 경로로 import

__all__ = [
    "StudyGroup",
    "GroupMember",
    "StudyLecture",
]

# __init__ 사용
# models 디렉토리를 패키지화하여 프로젝트 구조 정리
# models import를 이용한 모델 일괄 참조