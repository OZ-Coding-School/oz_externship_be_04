from django.db import models

from apps.core.models import TimeStampedModel


class Review(TimeStampedModel):
    class StarRating(models.IntegerChoices):
        Five = 5, "5_OUT_OF_5_STARS"
        Four = 4, "4_OUT_OF_5_STARS"
        Three = 3, "3_OUT_OF_5_STARS"
        Two = 2, "2_OUT_OF_5_STARS"
        One = 1, "1_OUT_OF_5_STARS"

    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    study_group = models.ForeignKey("study_groups.StudyGroup", on_delete=models.CASCADE)

    star_rating = models.IntegerField(choices=StarRating.choices, null=False)
    content = models.CharField(max_length=300, null=False)

    class Meta:
        db_table = "reviews"
        constraints = [models.UniqueConstraint(fields=["user", "study_group"], name="unique_user_study_group_review")]
