from datetime import datetime
from typing import Any, Optional

from rest_framework import serializers

from apps.users.models import User


class AdminAccountSerializer(serializers.ModelSerializer[User]):
    """
    어드민 회원 목록 조회용 serializer
    """

    role = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    withdraw_at = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nickname",
            "name",
            "birthday",
            "status",
            "role",
            "withdraw_at",
            "created_at",
        ]

    def get_withdraw_at(self, obj: User) -> Optional[datetime]:
        withdrawal = obj.withdrawals.order_by("-created_at").first()
        if withdrawal is None:
            return None
        return withdrawal.created_at


class AdminAccountDetailReadSerializer(serializers.ModelSerializer[User]):
    """
    어드민 회원 정보 상세 조회용 serializer (Get 전용)
    """

    role = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "gender",
            "nickname",
            "birthday",
            "phone_number",
            "email",
            "role",
            "status",
            "created_at",
            "profile_img_url",
        ]


class AdminAccountDetailSerializer(serializers.ModelSerializer[User]):
    """
    어드민 회원 정보 상세 serializer
    """

    role = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "gender",
            "nickname",
            "birthday",
            "phone_number",
            "email",
            "role",
            "status",
            "created_at",
            "updated_at",
            "profile_img_url",
        ]


class AdminAccountUpdateSerializer(serializers.Serializer[Any]):
    """
    어드민 페이지 회원 정보 수정 요청용 Serializer
    """

    nickname = serializers.CharField(
        required=False,
        max_length=10,
        help_text="닉네임",
    )
    name = serializers.CharField(
        required=False,
        max_length=30,
        help_text="이름",
    )
    phone_number = serializers.RegexField(
        regex=r"^\d{11}$",
        required=False,
        error_messages={"invalid": "11자리 숫자로 구성해야 합니다."},
        help_text="휴대폰 번호(예: 01012349876)",
    )
    birthday = serializers.DateField(required=False, help_text="생년월일 (예: 2001-09-07)")
    gender = serializers.ChoiceField(required=False, choices=[("M", "M"), ("F", "F")], help_text="성별 (M/F 선택)")
    is_active = serializers.BooleanField(required=False, help_text="계정 활성화 여부")
    profile_img_url = serializers.URLField(required=False, help_text="프로필 이미지 URL")


class AdminAccountRoleUpdateSerializer(serializers.Serializer[Any]):
    """
    어드민 페이지에서 유저의 권한을 변경할 때 사용하는 요청 바디용 Serializer
    """

    role = serializers.ChoiceField(
        choices=[
            ("user", "user"),
            ("staff", "staff"),
            ("admin", "admin"),
        ],
        help_text="변경할 권한 (user, staff, admin)",
    )
