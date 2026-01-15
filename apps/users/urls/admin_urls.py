from django.urls import path

from apps.users.views.admin_account_view import (
    AdminAccountActivateView,
    AdminAccountDetailSpec,
    AdminAccountListSpec,
    AdminAccountRoleUpdateSpec,
)
from apps.users.views.admin_signup_trends_view import AdminSignupTrendView
from apps.users.views.admin_withdrawal_reason_trends_view import (
    AdminWithdrawalReasonMonthlyStatsView,
    AdminWithdrawalReasonPercentageView,
)
from apps.users.views.admin_withdrawal_view import (
    AdminWithdrawalDetail,
    AdminWithdrawalList,
)
from apps.users.views.admin_withdrawals_trends_view import AdminWithdrawalTrendSpec

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
    path(
        "/admin/account/<int:account_id>/activate",
        AdminAccountActivateView.as_view(),
        name="admin_account_activate",
    ),
    path(
        "/admin/withdrawals",
        AdminWithdrawalList.as_view(),
        name="admin_withdrawal_list",
    ),
    path(
        "/admin/withdrawals/<int:withdrawal_id>",
        AdminWithdrawalDetail.as_view(),
        name="admin_withdrawal_detail",
    ),
    path(
        "/admin/analytics/signup/trends",
        AdminSignupTrendView.as_view(),
        name="admin_signup_trends",
    ),
    path(
        "/admin/analytics/withdrawals/trends",
        AdminWithdrawalTrendSpec.as_view(),
        name="admin_withdrawal_trends",
    ),
    path(
        "/admin/analytics/withdrawal-reasons/percentage",
        AdminWithdrawalReasonPercentageView.as_view(),
        name="admin_withdrawal_reason_percentage",
    ),
    path(
        "/admin/analytics/withdrawal-reasons/stats/monthly",
        AdminWithdrawalReasonMonthlyStatsView.as_view(),
        name="admin_withdrawal_reasons_stats_monthly",
    ),
]
