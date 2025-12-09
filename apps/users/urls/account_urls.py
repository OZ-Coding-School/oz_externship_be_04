from django.urls import path

from apps.users.views.user_account_views import UserAccountView
from apps.users.views.user_register import SignupView

urlpatterns = [
    path("accounts/me", UserAccountView.as_view(), name="account"),
    path("accounts/signup", SignupView.as_view(), name="signup"),
]
