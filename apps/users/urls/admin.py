from django.urls import path

from apps.users.views.admin_account_spec import AdminAccountListSpec

urlpatterns = [
    path(
        "accounts",
        AdminAccountListSpec.as_view(),
        name="admin_account_list",
    ),
]
