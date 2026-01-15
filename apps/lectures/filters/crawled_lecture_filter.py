from django_filters import CharFilter, FilterSet

from apps.lectures.models import CrawledLecture


class CrawledLectureFilter(FilterSet):
    category = CharFilter(field_name="lecture_categories__category__name", lookup_expr="iexact")

    class Meta:
        model = CrawledLecture
        fields = ["category"]
