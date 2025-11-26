from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

from apps.core.models import BaseModel


class GenderChoices(models.TextChoices):
    MALE = "M", "남성"
    FEMALE = "F", "여성"


class User(BaseModel, AbstractBaseUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=30)
    nickname = models.CharField(max_length=10, unique=True)
    phone_number = models.CharField(max_length=20, unique=True)
    gender = models.CharField(max_length=1, choices=GenderChoices.choices)
    birthday = models.DateField()
    profile_img_url = models.URLField(max_length=255)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    USERNAME_FIELD = "email"

    class Meta:
        db_table = "users"
