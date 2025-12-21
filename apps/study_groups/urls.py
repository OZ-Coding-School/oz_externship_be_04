from django.urls import path

from .views.admin_review_view import (
    AdminStudyReviewDetailAPIView,
    AdminStudyReviewListAPIView,
)

# from .views.admin_study_groups_view import (
#     AdminStudyGroupDetailView,
#     AdminStudyGroupListView,
# )
from .views.review_view import (
    StudyGroupReviewCreateAPIView,
    StudyGroupReviewUpdateAPIView,
)
from .views.schedule_views import (
    ScheduleDetailView,
    ScheduleView,
)
from .views.study_groups_view import (
    DelegateLeaderAPIView,
    KickStudyGroupMemberAPIView,
    LeaveStudyGroupMeAPIView,
    StudyGroupListCreateAPIView,
    StudyGroupRetrieveUpdateDestroyAPIView,
)
from .views.study_note import (
    StudyNoteDetailView,
    StudyNoteListCreateView,
)

urlpatterns = [
    # StudyGroup Admin
    # path("/admin/study-groups", AdminStudyGroupListView.as_view(), name="admin-study-group-list"),
    # path(
    #     "/admin/study-groups/<int:study_group_id>", AdminStudyGroupDetailView.as_view(), name="admin-study-group-detail"
    # ),
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
    path("/study-groups/<int:group_id>/schedules", ScheduleView.as_view(), name="schedule"),
    path(
        "/study-groups/<int:group_id>/schedules/<int:schedule_id>", ScheduleDetailView.as_view(), name="schedule-detail"
    ),
    path("/study-groups/<int:group_id>/notes", StudyNoteListCreateView.as_view(), name="study-note-list-create"),
    path("/study-groups/<int:group_id>/notes/<int:note_id>", StudyNoteDetailView.as_view(), name="study-note-detail"),
    path(
        "/admin/study-reviews/<int:review_id>",
        AdminStudyReviewDetailAPIView.as_view(),
        name="admin-study-review-detail",
    ),
    path("/admin/study-reviews", AdminStudyReviewListAPIView.as_view(), name="admin-study-review-list"),
]
