from .recruitment_bookmarks import urlpatterns as bookmarks_patterns
from .recruitment_tags import urlpatterns as tags_urlpatterns

urlpatterns = bookmarks_patterns + tags_urlpatterns
