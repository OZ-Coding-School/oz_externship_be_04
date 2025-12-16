from django.urls import path

<<<<<<< HEAD
from .views.review_view import (
    StudyGroupReviewCreateAPIView,
    StudyGroupReviewUpdateAPIView,
)
=======
from .views import StudyNoteAPIView, StudyNoteDetailAPIView
<<<<<<< HEAD
>>>>>>> 52d1f99 (노트 작성/목록 API와 테스트 추가)
=======
from .views.review_view import StudyGroupReviewCreateAPIView, StudyGroupReviewUpdateAPIView
>>>>>>> bfdf286 (pr 피드백 반영)
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
    path("/study-groups/create", StudyGroupCreateAPIView.as_view(), name="study-group-create"),
<<<<<<< HEAD
    path("/study-groups/<int:group_id>/reviews", StudyGroupReviewCreateAPIView.as_view(), name="study-group-review"),
    path(
        "/study-groups/<int:group_id>/reviews/<int:review_id>",
        StudyGroupReviewUpdateAPIView.as_view(),
        name="study-group-review-update",
    ),
    path("/study-groups", StudyGroupCreateAPIView.as_view(), name="study-group-create"),
    path("/study-groups/<int:group_id>", StudyGroupRetrieveAPIView.as_view(), name="study-group-detail"),
    path("/study-groups/<int:group_id>", StudyGroupUpdateAPIView.as_view(), name="study-group-update"),
    path("/study-groups/<int:group_id>", StudyGroupDestroyAPIView.as_view(), name="study-group-delete"),
    path("/study-groups/<int:group_id>/delegate-leader", DelegateLeaderAPIView.as_view(), name="delegate-leader"),
=======
    path("/study-groups/<int:pk>", StudyGroupRetrieveAPIView.as_view(), name="study-group-detail"),
    path("/study-groups/<int:pk>/update", StudyGroupUpdateAPIView.as_view(), name="study-group-update"),
    path("/study-groups/<int:pk>/delete", StudyGroupDestroyAPIView.as_view(), name="study-group-delete"),
    path(
        "/study-groups/<int:group_id>/delegate-leader",
        DelegateLeaderAPIView.as_view(),
        name="delegate-leader",
    ),
>>>>>>> 52d1f99 (노트 작성/목록 API와 테스트 추가)
    path(
        "/study-groups/<int:group_id>/reviews",
        StudyGroupReviewCreateAPIView.as_view(),
        name="study-group-review",
    ),
    path(
        "/study-groups/<int:group_id>/reviews/<int:review_id>",
        StudyGroupReviewUpdateAPIView.as_view(),
        name="study-group-review-update",
    ),
    path(
        "/study-groups/<int:group_id>/members/<int:member_id>",
        KickStudyGroupMemberAPIView.as_view(),
        name="study-group-kick",
    ),
    path(
        "/study-groups/<int:group_id>/members/me",
        LeaveStudyGroupMeAPIView.as_view(),
        name="study-group-leave",
    ),
    path(
        "/study-groups/<int:study_group_id>/notes",
        StudyNoteAPIView.as_view(),
        name="study-note",
    ),
    path(
        "/study-groups/<int:study_group_id>/notes/<int:note_id>",
        StudyNoteDetailAPIView.as_view(),
        name="study-note-detail",
    ),
]
