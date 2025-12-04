from django.urls import path

from apps.users.views.admin_account_spec import (
    AdminAccountDetailSpec,
    AdminAccountListSpec,
)

urlpatterns = [
    path(
        "/admin/account",
        AdminAccountListSpec.as_view(),
        name="admin_account_list",
    ),
    path(
        "/admin/account/<int:account_id>",
        AdminAccountDetailSpec.as_view(),
        name="admin_account_detail",
    ),
]
