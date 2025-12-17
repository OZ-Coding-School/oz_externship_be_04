from django.urls import path

from .views.review_view import (
    StudyGroupReviewCreateAPIView,
    StudyGroupReviewUpdateAPIView,
)
from .views.study_groups_view import (
    DelegateLeaderAPIView,
    KickStudyGroupMemberAPIView,
    LeaveStudyGroupMeAPIView,
    StudyGroupListCreateAPIView,
    StudyGroupRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    # StudyGroup
    path("/study-groups", StudyGroupListCreateAPIView.as_view(), name="study-group-list-create"),
    path("/study-groups/<int:group_id>", StudyGroupRetrieveUpdateDestroyAPIView.as_view(), name="study-group-rud"),
    # GroupMember 관리
    path("/study-groups/<int:group_id>/delegate-leader", DelegateLeaderAPIView.as_view(), name="delegate-leader"),
    path(
        "/study-groups/<int:group_id>/members/<int:member_id>",
        KickStudyGroupMemberAPIView.as_view(),
        name="study-group-kick",
    ),
    path("/study-groups/<int:group_id>/members/me", LeaveStudyGroupMeAPIView.as_view(), name="study-group-leave"),
    # Review
    path("/study-groups/<int:group_id>/reviews", StudyGroupReviewCreateAPIView.as_view(), name="study-group-review"),
    path(
        "/study-groups/<int:group_id>/reviews/<int:review_id>",
        StudyGroupReviewUpdateAPIView.as_view(),
        name="study-group-review-update",
    ),
]
