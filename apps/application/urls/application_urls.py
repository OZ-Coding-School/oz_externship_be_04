from django.urls import path

from apps.application.views.admin_application_views import (
    AdminApplicationDetailView,
    AdminApplicationListView,
)
from apps.application.views.applicant_application_views import (
    ApplicationCancelView,
    ApplicationCreateView,
    ApplicationDeleteView,
    MyApplicationDetailView,
    MyApplicationListView,
)
from apps.application.views.recruiter_application_views import (
    ApplicationAcceptView,
    ApplicationListView,
    ApplicationRejectView,
    ApplicationReviewView,
)

urlpatterns = [
    # Applicant
    path(
        "recruitments/<str:recruitment_uuid>/applications", ApplicationCreateView.as_view(), name="application-create"
    ),
    path("applications/mine", MyApplicationListView.as_view(), name="application-list-mine"),
    path("applications/<int:application_id>", MyApplicationDetailView.as_view(), name="application-detail"),
    path("applications/<int:application_id>/cancel", ApplicationCancelView.as_view(), name="application-cancel"),
    path("applications/<int:application_id>", ApplicationDeleteView.as_view(), name="application-delete"),
    # Recruiter
    path(
        "recruitments/<str:recruitment_uuid>/applicants",
        ApplicationListView.as_view(),
        name="recruiter-application-list",
    ),
    path(
        "applications/<int:application_id>/review",
        ApplicationReviewView.as_view(),
        name="recruiter-application-review",
    ),
    path(
        "applications/<int:application_id>/accept",
        ApplicationAcceptView.as_view(),
        name="recruiter-application-accept",
    ),
    path(
        "applications/<int:application_id>/reject",
        ApplicationRejectView.as_view(),
        name="recruiter-application-reject",
    ),
    # Admin
    path("admin/applications", AdminApplicationListView.as_view(), name="admin-application-list"),
    path(
        "admin/applications/<int:application_id>",
        AdminApplicationDetailView.as_view(),
        name="admin-application-detail",
    ),
]
