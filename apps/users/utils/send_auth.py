from django.core.mail import send_mail
from rest_framework import status
from rest_framework.response import Response

from apps.users.utils.auth_code import AuthCodeCache
from config.settings.base import DEFAULT_FROM_EMAIL

class SendAuth:
    TEMPLATES = {
        "signup": {
            "subject": "회원가입 이메일 인증",
            "message": "{code}"
        },
        "reset_password": {
            "subject": "비밀번호 재설정 이메일 인증",
            "message":"{code}"
        },
        "restore": {
            "subject": "계정 복구 이메일 인증",
            "message": "{code}"
        }
    }
    @classmethod
    def send_email_auth(cls, email: str, auth_type: str) ->Response:
        try:
            template = cls.TEMPLATES[auth_type]
            if not template:
                return Response(
                    {"error_detail": "잘못된 접근입니다"},
                            status=status.HTTP_400_BAD_REQUEST)
            code = AuthCodeCache.generate_mail_code(6)
            key = f"email:{auth_type}:{email}"
            AuthCodeCache.save(key, code, expires_time=300)
            send_mail(
                subject=template["subject"],
                message=template["message"].format(code=code),
                from_email=DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
         )
            return Response({"detail":"이메일 발송완료"})
        except Exception as e:
            return Response({"error_detail": f"이메일 발송실패: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @classmethod
    def send_signup_email(cls, email: str) -> Response:
        return cls.send_email_auth(email, "signup")

    @classmethod
    def send_password_reset_email(cls, email: str) -> Response:
        return cls.send_email_auth(email, "reset_password")

    @classmethod
    def send_restore_email(cls, email: str) -> Response:
        return cls.send_email_auth(email, "restore")