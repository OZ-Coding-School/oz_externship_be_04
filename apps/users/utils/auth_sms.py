import os
import random

from dotenv import load_dotenv
from rest_framework.response import Response
from rest_framework.views import APIView
from twilio.rest import Client

load_dotenv()


def generator_random_number():
    return random.randrange(100000, 999999)


class TwilioSendSMS(APIView):
    def post(self, request):
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        api_secret = os.getenv("MY_API_SECRET")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_number = os.getenv("PURCHAESE_NUMBER")  # 구입한 번호

        my_phone_number = os.getenv("MY_PHONE_NUMBER")  # 내폰번호 테스트용
        client = Client(account_sid, api_secret, auth_token)

        # phone = request.POST.get("phone_number")
        random_number = generator_random_number()

        # redis.set(phone, random_number)

        message = client.messages.create(
            body=f"{random_number}인증번호 입니다 화면에 6자리숫자를 입력해주세요",
            from_=twilio_number,
            to=my_phone_number,
        )

        return Response(status_code=200)


#
#
# account_sid = os.getenv('TWILIO_ACCOUNT_SID')
# auth_token = os.getenv('TWILIO_AUTH_TOKEN')
# twilio_number = os.getenv('TWILIO_NUMBER')
# my_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
# client = Client(account_sid, auth_token)
# message = client.messages.create(
#     body="test message",
#     from_=twilio_number,
#     to=my_phone_number
# )
#
# print(message.body)

import re
from random import randint

import requests
from django.http import JsonResponse
from django.views import View
from my_settings import ACCOUNT_SID, AUTH_TOKEN
from twilio.rest import Client
from users.models import PhoneCheck, User


class SendSmSView(View):
    def post(self, request):
        try:
            # 멘토님의 리뷰수정을 거듭하며 try를 사용법에 대해 조금 더 알게 되었다.
            data = json.loads(request.body)
            input_mobile = data["mobile"]

            if not re.match(r"(010)\d{4}\d{4}", input_mobile):
                return JsonResponse({"message": "INVALID_PHONE_NUMBER"}, status=401)
            to_mobile = "+82" + input_mobile[1:]
            # 메세지를 보내기 위해 번호 +821012344321 형식으로 변경
            check_number = randint(1000, 9999)
            # 인증번호 무작위 생성

            if not PhoneCheck.objects.filter(check_id=input_mobile).exists():
                PhoneCheck.objects.create(check_id=input_mobile, check_number=check_number)
            PhoneCheck.objects.filter(check_id=input_mobile).update(check_number=check_number)
            # 인증 핸드폰 및 인증 번호 DB 생성, 인증 핸드폰 번호 존재 시 인증번호 업데이트
            # else 사용을 최대한 줄이는 연습을 해야함!

            client = Client(ACCOUNT_SID, AUTH_TOKEN)
            client.messages.create(
                body=f"milliem의사서 인증을 위해 [{check_number}]을 입력해주세요.", from_="+14078716367", to=to_mobile
            )
            # twilio에서 제공하는 외부 API
            return JsonResponse({"message": "SUCCESS"}, status=200)
        except KeyError:
            return JsonResponse({"message": "KEY_ERROR"}, status=401)
