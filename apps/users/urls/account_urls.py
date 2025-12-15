from django.urls import path

from apps.users.views.user_account_views import (
    NicknameCheckView,
    UserAccountView,
    UserPasswordResetView,
)
from apps.users.views.user_login_view import LoginView
from apps.users.views.user_register import SignupView

urlpatterns = [
    path("accounts/me", UserAccountView.as_view(), name="account"),
    path("accounts/signup", SignupView.as_view(), name="signup"),
    path("accounts/check-nickname", NicknameCheckView.as_view(), name="check-nickname"),
    path("accounts/find-password", UserPasswordResetView.as_view(), name="find-password"),
    path("accounts/login", LoginView.as_view(), name="login"),
]
