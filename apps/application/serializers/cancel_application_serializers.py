from __future__ import annotations

from rest_framework import serializers
from apps.application.models import Application

class ApplicationCancelSerializer(serializers.ModelSerializer["Application"]):
    """
    REQ-APLY-008: 지원 취소 응답 전용 시리얼라이저
    취소 완료 후, 변경된 상태와 UUID만 반환하여 응답을 경량화
    """
    class Meta:
        model = Application
        fields = ["uuid", "status"]
        read_only_fields = ["uuid", "status"]