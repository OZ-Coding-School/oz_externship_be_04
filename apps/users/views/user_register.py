from drf_spectacular.utils import extend_schema, OpenApiExample, inline_serializer
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.user_serializer import UserSerializer


class SignupView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=['Account'],
        summary="회원가입 API",
        description="새로운 사용자 등록",
        request=inline_serializer(
            name="SignUpRequest",
            fields={
                "email":serializers.EmailField(required=True),
                "password":serializers.CharField(required=True),
                "nickname":serializers.CharField(required=True),
                "name":serializers.CharField(required=True),
                "phone_number":serializers.CharField(required=True,help_text="010-1234-5678,01012345678"),
                "birthday":serializers.DateField(required=True,help_text="YYYY-MM-DD"),
                "gender":serializers.ChoiceField(choices=["M","F"],required=True),
            }
        ),
        examples=[
            OpenApiExample(
                name="SignUp",
                value={
                    "email":"example@example.com",
                    "password":"str",
                    "nickname":"str",
                    "name":"str",
                    "phone_number":"010-1234-5678,01012345678",
                    "birthday":"1991-12-22",
                    "gender":"M",
                }
            )
        ],
        responses={
            201 : inline_serializer(
                name="SignUpSuccess",
                fields={"detail" : serializers.CharField()},
            ),
            400 : inline_serializer(
                name="SignUpValidationError",
                fields={
                    "error_detail": serializers.DictField(
                        child=serializers.ListField(
                            child=serializers.CharField()
                        )
                    ),
                }
            ),
            409 : inline_serializer(
                name="SignUpValidationError",
                fields={
                    "error_detail": serializers.CharField()
                }
            )
        },
    )


    def post(self, request: Request) -> Response:
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail":"회원가입 완료"},status=status.HTTP_201_CREATED)
        return Response({"error_detail":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

