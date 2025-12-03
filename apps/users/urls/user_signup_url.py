from django.urls import path

from apps.users.views.user_register import SignupView

urlpatterns = [
    path("accounts/signup", SignupView.as_view(), name="signup"),
]
