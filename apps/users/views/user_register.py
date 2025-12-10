from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.user_serializer import UserSerializer


class SignupView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="회원가입 API",
        description="새로운 사용자 등록",
        request=inline_serializer(
            name="SignUpRequest",
            fields={
                "email": serializers.EmailField(required=True),
                "password": serializers.CharField(required=True),
                "nickname": serializers.CharField(required=True),
                "name": serializers.CharField(required=True),
                "phone_number": serializers.CharField(required=True, help_text="010-1234-5678,01012345678"),
                "birthday": serializers.DateField(required=True, help_text="YYYY-MM-DD"),
                "gender": serializers.ChoiceField(choices=["M", "F"], required=True),
            },
        ),
        examples=[
            OpenApiExample(
                name="SignUp",
                value={
                    "email": "example@example.com",
                    "password": "str",
                    "nickname": "str",
                    "name": "str",
                    "phone_number": "010-1234-5678,01012345678",
                    "birthday": "1991-12-22",
                    "gender": "M",
                },
            )
        ],
        responses={
            201: inline_serializer(
                name="SignUpSuccess",
                fields={"detail": serializers.CharField()},
            ),
            400: inline_serializer(
                name="SignUpValidationError",
                fields={"error_detail": serializers.CharField()},
            ),
            409: inline_serializer(name="SignUpConflictError", fields={"error_detail": serializers.CharField()}),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "회원가입 완료"}, status=status.HTTP_201_CREATED)

        first_error = list(serializer.errors.values())[0][0]

        if "이미 사용 중인" in first_error:
            return Response(
                {"error_detail": "이미 중복된 회원가입 내역이 존재합니다."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response({"error_detail": first_error}, status=status.HTTP_400_BAD_REQUEST)
