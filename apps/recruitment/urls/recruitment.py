from django.urls import path

from apps.recruitment.views.recruitment_view import (
    RecruitmentDetailUpdateDeleteView,
    RecruitmentListCreateView,
    RecruitmentMineView,
)

urlpatterns = [
    # 공고 목록 및 작성 (GET: 목록, POST: 작성)
    path("recruitments/", RecruitmentListCreateView.as_view(), name="recruitment-list-create"),
    # 내가 작성한 공고 (GET)
    path("recruitments/mine/", RecruitmentMineView.as_view(), name="recruitment-mine"),
    # 공고 상세/수정/삭제 (GET: 상세, PATCH: 수정, DELETE: 삭제)
    path(
        "recruitments/<uuid:recruitments_uuid>/", RecruitmentDetailUpdateDeleteView.as_view(), name="recruitment-detail"
    ),
]
