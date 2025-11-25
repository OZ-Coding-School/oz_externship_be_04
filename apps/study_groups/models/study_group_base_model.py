from django.db import models


class StudyGroupBaseModel(models.Model):
    class StudyGroupStatusChoices(models.TextChoices):
        PENDING = "PENDING"
        ONGOING = "ONGOING"
        ENDED = "ENDED"

    name = models.CharField(max_length=20)
    introduction = models.CharField(max_length=500, blank=True, null=True)
    max_headcount = models.SmallIntegerField()
    profile_img_url = models.URLField(blank=True, null=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(
        choices=StudyGroupStatusChoices.choices,
        max_length=8,
        default=StudyGroupStatusChoices.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 처음 생성 시에만 자동 저장
    updated_at = models.DateTimeField(auto_now=True)  # 갱신 시 저장

    class Meta:
        db_table = "study_group"

    def __str__(self) -> str:
        return self.name
