from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.views.user_register import UserLoginAPIView, UserRegisterAPIView

urlpatterns = [
    path("sign-up/", UserRegisterAPIView.as_view(), name="user-sign-up"),
    path("sign-in/", UserLoginAPIView.as_view(), name="user-sign-in"),
    path("refresh/", TokenRefreshView.as_view(), name="user-token-refresh"),
]