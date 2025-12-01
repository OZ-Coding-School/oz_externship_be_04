from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView, status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import Token

from apps.users.serializers.user_register_serializers import UserLoginSerializer, UserRegisterSerializer


class UserRegisterAPIView(APIView):
    def post(self, request: Request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token: Token = TokenObtainPairSerializer.get_token(user)
            res = Response(
                {
                    "user": serializer.data,
                    "message": "register successs",
                    "token": {
                        "access": str(token.access_token),
                        "refresh": str(token),
                    },
                },
                status=status.HTTP_200_OK,
            )
            return res
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginAPIView(APIView):
    def post(self, request: Request):
        token_serializer = TokenObtainPairSerializer(data=request.data)
        if token_serializer.is_valid():
            user = token_serializer.user
            serializer = UserLoginSerializer(user)
            return Response(
                {
                    "user": serializer.data,
                    "message": "login success",
                    "token": token_serializer.validated_data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(token_serializer.errors, status=status.HTTP_400_BAD_REQUEST)