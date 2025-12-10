from apps.core import models


class Verify(models.Model):
    email = models.EmailField()
    athnt_code = models.CharField(max_length=6)
