from django.urls import path

from .views.study_groups_view import (
    DelegateLeaderAPIView,
    KickStudyGroupMemberAPIView,
    LeaveStudyGroupMeAPIView,
    StudyGroupCreateAPIView,
    StudyGroupDestroyAPIView,
    StudyGroupListAPIView,
    StudyGroupRetrieveAPIView,
    StudyGroupUpdateAPIView,
)

urlpatterns = [
    path("/study-groups", StudyGroupListAPIView.as_view(), name="study-group-list"),
    path("/study-groups", StudyGroupCreateAPIView.as_view(), name="study-group-create"),
    path("/study-groups/<int:group_id>", StudyGroupRetrieveAPIView.as_view(), name="study-group-detail"),
    path("/study-groups/<int:group_id>", StudyGroupUpdateAPIView.as_view(), name="study-group-update"),
    path("/study-groups/<int:group_id>", StudyGroupDestroyAPIView.as_view(), name="study-group-delete"),
    path("/study-groups/<int:group_id>/delegate-leader", DelegateLeaderAPIView.as_view(), name="delegate-leader"),
    path(
        "/study-groups/<int:group_id>/members/<int:member_id>",
        KickStudyGroupMemberAPIView.as_view(),
        name="study-group-kick",
    ),
    path("/study-groups/<int:group_id>/members/me", LeaveStudyGroupMeAPIView.as_view(), name="study-group-leave"),
]
