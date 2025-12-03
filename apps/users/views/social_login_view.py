from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers.oauth_serializers import SocialLoginSerializer
from apps.users.services.oauth_services import SocialLoginService


class SocialLoginView(APIView):
    def post(self, request):
        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = serializer.validated_data["provider"]
        user_info = {
            "provider_id": serializer.validated_data["provider_id"],
        }

        user, created = SocialLoginService().login_or_signup(provider, user_info)

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response(
            {
                "is_new_user": created,
                "access": str(access),
                "refresh": str(refresh),
                "user_id": user.id,
                "nickname": user.nickname,
            },
            status=status.HTTP_200_OK,
        )
