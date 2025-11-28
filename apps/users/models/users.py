from typing import Any, Optional

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models

from apps.core.models import TimeStampedModel


class UserManager(BaseUserManager["User"]):

    def create_user(self, email: str, password: Optional[str] = None, **extra_fields: Any) -> "User":
        if not email:
            raise ValueError("알맞은 이메일을 입력하세요.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: Optional[str] = None, **extra_fields: Any) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
          raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
          raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class GenderChoices(models.TextChoices):
    MALE = "M", "남성"
    FEMALE = "F", "여성"


class User(TimeStampedModel, AbstractBaseUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=30)
    nickname = models.CharField(max_length=10, unique=True)
    phone_number = models.CharField(max_length=20, unique=True)
    gender = models.CharField(max_length=1, choices=GenderChoices.choices)
    birthday = models.DateField()
    profile_img_url = models.URLField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname", "name", "phone_number", "birthday", "gender"]

    _status_value: Optional[str] = None

    @property
    def status_value(self) -> Optional[str]:
        return self._status_value

    @status_value.setter
    def status_value(self, value: Optional[str]) -> None:
        self._status_value = value

    class Meta:
        db_table = "users"
