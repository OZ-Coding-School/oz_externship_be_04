from django.urls import path
from apps.study_groups.views.schedule_create_view import (
    ScheduleListCreateView
)

urlpatterns = [
    path("<int:group_id>/schedules/", ScheduleListCreateView.as_view()),
    ]