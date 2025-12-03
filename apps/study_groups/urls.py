from django.urls import path
from apps.study_groups.views.schedule_views import ScheduleCreateView

urlpatterns = [
    path("<int:group_id>/schedules/", ScheduleCreateView.as_view()),
]