from django.urls import path

from apps.users.views.user_account_views import NicknameCheckView, UserAccountView
from apps.users.views.user_register import SignupView

urlpatterns = [
    path("accounts/me", UserAccountView.as_view(), name="account"),
    path("accounts/signup", SignupView.as_view(), name="signup"),
    path("accounts/check-nickname", NicknameCheckView.as_view(), name="check-nickname"),
]
