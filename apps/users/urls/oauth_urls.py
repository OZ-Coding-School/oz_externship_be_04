from django.urls import path
from apps.users.views.oauth_views import KakaoLoginView

urlpatterns = [
    path("kakao/login/", KakaoLoginView.as_view(), name="kakao-login"),
]