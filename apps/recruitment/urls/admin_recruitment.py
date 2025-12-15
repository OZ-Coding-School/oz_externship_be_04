from django.urls import path

from apps.recruitment.views.recruitment_admin_view import (
    AdminRecruitmentDetailView,
    AdminRecruitmentListView,
)

urlpatterns = [
    path("admin/recruitments", AdminRecruitmentListView.as_view(), name="admin-recruitment-list"),
    path(
        "admin/recruitments/<int:recruitment_id>",
        AdminRecruitmentDetailView.as_view(),
        name="admin-recruitment-detail",
    ),
]
