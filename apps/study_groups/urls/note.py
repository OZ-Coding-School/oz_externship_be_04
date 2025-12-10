from django.urls import path

from apps.study_groups.views import StudyNoteCreateAPIView

urlpatterns = [
    path("<int:study_group_id>/notes/", StudyNoteCreateAPIView.as_view(), name="study-note-create"),
]
