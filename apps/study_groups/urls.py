from django.urls import path

from .views.study_groups_view import (
    StudyGroupCreateAPIView,
    StudyGroupDestroyAPIView,
    StudyGroupListAPIView,
    StudyGroupRetrieveAPIView,
    StudyGroupUpdateAPIView,
)

urlpatterns = [
    path("/study-groups", StudyGroupListAPIView.as_view(), name="study-group-list"),
    path("/study-groups/create", StudyGroupCreateAPIView.as_view(), name="study-group-create"),
    path("/study-groups/<int:pk>", StudyGroupRetrieveAPIView.as_view(), name="study-group-detail"),
    path("/study-groups/<int:pk>/update", StudyGroupUpdateAPIView.as_view(), name="study-group-update"),
    path("/study-groups/<int:pk>/delete", StudyGroupDestroyAPIView.as_view(), name="study-group-delete"),
]
