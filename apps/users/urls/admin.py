from django.urls import path

from apps.users.views.admin_account_spec import AdminAccountListSpec

urlpatterns = [
    path(
        "members/spec/",
        AdminAccountListSpec.as_view(),
        name="admin_account_list",
    ),
]