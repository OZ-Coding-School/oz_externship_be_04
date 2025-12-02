from django.urls import path

from apps.study_groups.views.schedule_create_view import ScheduleCreateView

app_name = "study_groups"

urlpatterns = [
    path("<int:group_id>/schedules/", ScheduleCreateView.as_view(), name="schedule_create"),
]
