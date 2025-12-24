from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from twilio.rest import Client  # type: ignore[import-untyped]

from apps.users.utils.conts import SMS_SEND_MESSAGE, SMS_VERIFY_MESSAGE
from config.settings.base import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_VERIFY_SERVICE_SID,
)


class TwilioSendSms:
    send_message = SMS_SEND_MESSAGE
    verify_message = SMS_VERIFY_MESSAGE

    def __init__(self) -> None:
        self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        self.verify_service_sid = TWILIO_VERIFY_SERVICE_SID

    def trans_phone_number(self, phone_number: str) -> str:
        phone_number = phone_number.replace("-", "").replace(" ", "")

        if phone_number.startswith("01"):
            return phone_number.replace("01", "+821", 1)
        return phone_number

    def send_sms_auth(self, phone_number: str, auth_type: str) -> Response:
        try:
            formatted_number = self.trans_phone_number(phone_number)

            verification = self.client.verify.v2.services(self.verify_service_sid).verifications.create(
                to=formatted_number, channel="sms"
            )
            if verification.status == "pending":
                message = self.send_message.get(auth_type, "휴대폰 인증 코드가 전송되었습니다.")
                return Response({"detail": message}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error_detail": f"발송 실패: {verification.status}"}, status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response({"error_detail": f"SMS 발송 실패: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def verify_sms_code(self, phone_number: str, code: str, auth_type: str) -> Response:
        try:
            formatted_number = self.trans_phone_number(phone_number)

            verification_check = self.client.verify.v2.services(self.verify_service_sid).verification_checks.create(
                to=formatted_number, code=code
            )

            if verification_check.status == "approved":
                cache_key = f"sms_verified:{auth_type}:{phone_number}"
                cache.set(cache_key, True, timeout=1800)  # 30분

                message = self.verify_message.get(auth_type, "휴대폰 인증에 성공하였습니다.")
                return Response({"detail": message}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error_detail": "인증 실패: 코드가 일치하지 않거나 만료되었습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            return Response({"error_detail": f"인증 실패: {e}"}, status=status.HTTP_400_BAD_REQUEST)

    @classmethod
    def send_signup_sms(cls, phone_number: str) -> Response:
        instance = cls()
        return instance.send_sms_auth(phone_number, "signup")

    @classmethod
    def send_find_email_sms(cls, phone_number: str) -> Response:
        instance = cls()
        return instance.send_sms_auth(phone_number, "find_email")

    @classmethod
    def send_reset_password_sms(cls, phone_number: str) -> Response:
        instance = cls()
        return instance.send_sms_auth(phone_number, "reset_password")

    @classmethod
    def send_change_phone_sms(cls, phone_number: str) -> Response:
        instance = cls()
        return instance.send_sms_auth(phone_number, "change_phone")

    @classmethod
    def verify_code(cls, phone_number: str, code: str, auth_type: str) -> Response:
        instance = cls()
        return instance.verify_sms_code(phone_number, code, auth_type)

    @classmethod
    def is_verified(cls, phone_number: str, auth_type: str) -> bool:
        cache_key = f"sms_verified:{auth_type}:{phone_number}"
        return bool(cache.get(cache_key, False))

    @classmethod
    def clear_verification(cls, phone_number: str, auth_type: str) -> None:
        cache_key = f"sms_verified:{auth_type}:{phone_number}"
        cache.delete(cache_key)
