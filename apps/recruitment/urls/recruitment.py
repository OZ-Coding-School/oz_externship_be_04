from django.urls import path

from apps.recruitment.views.recruitment_view import (
    RecruitmentCreateView,
    RecruitmentDeleteView,
    RecruitmentDetailView,
    RecruitmentListView,
    RecruitmentMineView,
    RecruitmentRecommandView,
    RecruitmentUpdateView,
)

urlpatterns = [
    # 공고 목록 및 작성
    path("/recruitments", RecruitmentListView.as_view(), name="recruitment-list"),
    path("/recruitments", RecruitmentCreateView.as_view(), name="recruitment-create"),
    # 추천 공고
    path("/recruitments/recommands", RecruitmentRecommandView.as_view(), name="recruitment-recommands"),
    # 내가 작성한 공고
    path("/recruitments/mine", RecruitmentMineView.as_view(), name="recruitment-mine"),
    # 공고 상세/수정/삭제
    path("/recruitments/<uuid:recruitment_uuid>", RecruitmentDetailView.as_view(), name="recruitment-detail"),
    path("/recruitments/<uuid:recruitment_uuid>", RecruitmentUpdateView.as_view(), name="recruitment-update"),
    path("/recruitments/<uuid:recruitment_uuid>", RecruitmentDeleteView.as_view(), name="recruitment-delete"),
]
