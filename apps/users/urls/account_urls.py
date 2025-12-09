from django.urls import path

from apps.users.views.user_account_views import UserAccountView

urlpatterns = [
    path("accounts/me", UserAccountView.as_view(), name="account"),
]
