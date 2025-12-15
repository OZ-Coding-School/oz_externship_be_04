from django.urls import path

from apps.users.views.social_login_view import SocialLoginView

urlpatterns = [
    path("social/login/", SocialLoginView.as_view(), name="social_login"),
]
