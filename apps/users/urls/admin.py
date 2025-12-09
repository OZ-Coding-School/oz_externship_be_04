from django.urls import path

from apps.users.views.admin_account_spec import (
    AdminAccountDetailSpec,
    AdminAccountListSpec,
    AdminAccountRoleUpdateSpec,
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
    path(
        "/admin/account/<int:account_id>/role",
        AdminAccountRoleUpdateSpec.as_view(),
        name="admin_account_role_update",
    ),
]
