from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.study_groups.views.study_groups_view import StudyGroupViewSet

router = DefaultRouter()
router.register(r"study_groups", StudyGroupViewSet, basename="study_groups")

urlpatterns = [
    path("/", include(router.urls)),  # router URL 포함
]
