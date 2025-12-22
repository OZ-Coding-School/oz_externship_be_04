from django.urls import path

from apps.users.views.email_auth_views import (
    EmailSignUpVerifyView,
    EmailSignUpView,
    FindPasswordSendEmailView,
    FindPasswordVerifyEmailView,
)
from apps.users.views.oauth_views import (
    KakaoCallBackView,
    KakaoLoginView,
    NaverCallBackView,
    NaverLoginView,
)
from apps.users.views.restore_views import RestoreAccountView, RestoreSendEmailView
from apps.users.views.token_views import LogoutView, TokenRefreshView
from apps.users.views.user_account_views import (
    NicknameCheckView,
    UserAccountView,
    UserPasswordResetView,
)
from apps.users.views.user_login_view import LoginView
from apps.users.views.user_register import SignupView
from apps.users.views.user_sms_view import (
    ChangePhoneSendSMSView,
    ChangePhoneView,
    FindEmailSendSMSView,
    FindEmailView,
    SignupSendSMSView,
    SignupVerifySMSView,
)

urlpatterns = [
    path("accounts/me", UserAccountView.as_view(), name="account"),
    path("accounts/signup", SignupView.as_view(), name="signup"),
    path("accounts/signup/send-email", EmailSignUpView.as_view(), name="send-email"),
    path("accounts/signup/verify-email", EmailSignUpVerifyView.as_view(), name="verify-email"),
    path("accounts/check-nickname", NicknameCheckView.as_view(), name="check-nickname"),
    path("accounts/find-password", UserPasswordResetView.as_view(), name="find-password"),
    path("accounts/login", LoginView.as_view(), name="login"),
    path("accounts/logout", LogoutView.as_view(), name="logout"),
    path("accounts/token/refresh", TokenRefreshView.as_view(), name="token-refresh"),
    path("accounts/social-login/naver", NaverLoginView.as_view(), name="naver-login"),
    path("accounts/social-login/naver/callback", NaverCallBackView.as_view(), name="naver-callback"),
    path("accounts/social-login/kakao", KakaoLoginView.as_view(), name="kakao-login"),
    path("accounts/social-login/kakao/callback", KakaoCallBackView.as_view(), name="kakao-callback"),
    path("accounts/signup/send-sms", SignupSendSMSView.as_view(), name="signup-send-sms"),
    path("accounts/signup/verify-sms", SignupVerifySMSView.as_view(), name="signup-verify-sms"),
    path("accounts/find-email/send-sms", FindEmailSendSMSView.as_view(), name="find-email-send-sms"),
    path("accounts/change-phone/send-sms", ChangePhoneSendSMSView.as_view(), name="change-phone-send-sms"),
    path("accounts/change-phone", ChangePhoneView.as_view(), name="change-phone"),
    path("accounts/find-password/send-email", FindPasswordSendEmailView.as_view(), name="find-password-send-email"),
    path(
        "accounts/find-password/verify-email", FindPasswordVerifyEmailView.as_view(), name="find-password-verify-email"
    ),
    path("accounts/find-email", FindEmailView.as_view(), name="find_email"),
    path("accounts/restore", RestoreAccountView.as_view(), name="restore"),
    path("accounts/restore/send-email", RestoreSendEmailView.as_view(), name="restore-send-email"),
]
