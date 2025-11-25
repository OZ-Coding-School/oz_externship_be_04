from django.db import models

from apps.users.models import User


class GroupMember(models.Model):
    study_group_id = models.ForeignKey("study_groups.StudyGroup", on_delete=models.CASCADE)
    # 현재: 멤버가 있어도 스터디 그룹 삭제 가능 (멤버들 자동 Delete 처리)
    # 보호 필요 시: CASCADE-> PROTECT 변경
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    # 현재: 속해 있는 그룹이 있는 멤버도 계정 삭제 가능 (멤버 란에서 자동 Delete 처리)
    # 보호 필요 시: CASCADE-> PROTECT 변경
    is_leader = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)  # 처음 생성 시에만 자동 저장
    updated_at = models.DateTimeField(auto_now=True)  # 갱신 시 저장

    class Meta:
        db_table = "study_member"

    def __str__(self) -> str:
        return f"{self.study_group_id.name}의 멤버 {self.user_id.nickname}"
