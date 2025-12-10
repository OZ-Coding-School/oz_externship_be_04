from random import randint

from django.conf import settings
from django.contrib.messages.api import success
from django.core.mail import EmailMessage
from django.http import HttpResponse, request
from django.shortcuts import redirect, render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.models.verifiy_mail_model import Verify
from apps.users.serializers.verify_mail_serializer import VerifySerializer


class AuthCodeCreateView(APIView):
    def post(self, request):
        email = request.data.get("email", "")

        if User.objects.filter(email=email).exists():
            return Response({"message": "이미 가입된 이메일입니다."}, status=status.HTTP_400_BAD_REQUEST)

        athnt_code = str(randint(1, 999999)).zfill(6)

        message = EmailMessage(
            "ChangeART [Verification Code]",
            f"인증코드 [{athnt_code}]",
            "changeart@gmail.com",
            [email],
        )

        authen_Code = Verify(email=email, athnt_code=athnt_code)
        authen_Code.save()
        message.send()
        return Response({"message": "이메일을 보냈습니다."}, status=status.HTTP_200_OK)


# 이메일 인증
class SignupView(APIView):
    def post(self, request, UserSerializer=None):
        Verify = VerifySerializer(data=request.data)
        if Verify.is_valid():
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "가입완료!"}, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {"message": f"${serializer.errors}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response({"message": "인증번호 불일치"}, status=status.HTTP_400_BAD_REQUEST)


#
# def contact_view(request):
#     form = contact_view()
#     if request.method == "POST":
#         form = contact_view(request.POST)
#         if form.is_vaild():
#             form.save()
#             return redirect("success")
#         else:
#             render(request, "contact/contact.html", {form: form})
#     return render(request, "contact/contact.html", {"form": form})


# def contact_view(request):
#     form = ContactForm(request.POST or None)
#     success = False
#     if form.is_valid():
#         name = form.cleaned_data.get('name')
#         email = form.cleaned_data.get('email')
#         message = form.cleaned_data.get('message')
#         send_mail(
#             subject=f"new message from {name}",
#             message=message,
#             from_email=settings.EMAIL_HOST_USER,
#             recipient_list=[email],
#             fail_silently=False,
#         )
#         success = True
#         form = ContactForm()
#         return render(request, "contact/contact.html", {"form" : form, "success" : success})
#     return render(request, "contact/contact.html", {"form": form})


# class mailView(APIView):
#     def get(self, request):
#         send_mail(
#             '메일 제목',
#             '메일 메시지',
#         <your send email>,
#         ['<수신 email>'],
#         fail_silently=False
#         )
#         return Response(
#             {'detail': '메일 전송완료'},
#             status=status.HTTP_200_OK
#         )
