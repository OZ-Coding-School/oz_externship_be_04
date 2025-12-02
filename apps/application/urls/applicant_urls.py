from django.urls import path

from apps.application.views.applicant_application_views import (
    ApplicationCancelView,
    ApplicationCreateView,
    MyApplicationDetailView,
    MyApplicationListView,
)

urlpatterns = [
    # Applicant
    path(
        "recruitments/<str:recruitment_uuid>/applications", ApplicationCreateView.as_view(), name="application-create"
    ),
    path("applications/mine", MyApplicationListView.as_view(), name="application-list-mine"),
    path("applications/<str:application_uuid>", MyApplicationDetailView.as_view(), name="application-detail"),
    path("applications/<str:application_uuid>/cancel", ApplicationCancelView.as_view(), name="application-cancel"),
]
