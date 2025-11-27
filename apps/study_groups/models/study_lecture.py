from django.db import models

from apps.core.models import TimeStampedModel


class StudyLecture(TimeStampedModel):
    lecture_id = models.ForeignKey("lectures.CrawledLecture", on_delete=models.CASCADE)
    study_group_id = models.ForeignKey("study_groups.StudyGroup", on_delete=models.CASCADE)

    class Meta:
        db_table = "study_lectures"
