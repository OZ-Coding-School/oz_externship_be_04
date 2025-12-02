from django_filters import CharFilter, FilterSet


class CrawledLectureFilter(FilterSet):
    category = CharFilter(field_name="lecture_categories__category__name", lookup_expr="iexact")
