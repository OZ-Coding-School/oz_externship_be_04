import random
import string

from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django_twilio.views import message
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models.users import User
from apps.users.serializers.user_serializer import UserSerializer

base62_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
base = len(base62_chars)


def encode_base62(num):
    if num == 0:
        return base62_chars[0]
    result = []
    while num:
        num, remainder = divmod(num, base)
        result.append(base62_chars[remainder])
    return "".join(reversed(result))


def decode_base62(base62_str):
    num = 0
    for char in base62_str:
        num = num * base + base62_chars.index(char)
    return num


message = EmailMessage()
User = get_user_model()


def send_temp_password_email(user, temp_password):
    title = "메일 제목 입력"
    content = {
        "message": "메일 내용 입력",
    }
    receive_email = [user.email]
    from_email = "발송하는 메일 정보 입력"
    emailContent = render_to_string("email.html", content)

    emailObject = EmailMessage(subject=title, body=emailContent, to="EMAIL_HOST_USER", from_email=from_email)
    emailObject.content_subtype = "html"
    emailObject.send()


class auth_mail_View(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request) -> Response:
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            subject = "[" + serializer.data["email"] + "]의 인증코드"
            to = [serializer.data["email"]]
            # message =


#
#
# class SignupView(APIView):
#     def post(self, request, UserSerializer=None):
#         Verify = VerifySerializer(data=request.data)
#         if Verify.is_valid():
#             serializer = UserSerializer(data=request.data)
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response({"message": "가입완료!"}, status=status.HTTP_201_CREATED)
#             else:
#                 return Response(
#                     {"message": f"${serializer.errors}"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )
#         else:
#             return Response({"message": "인증번호 불일치"}, status=status.HTTP_400_BAD_REQUEST)
#
