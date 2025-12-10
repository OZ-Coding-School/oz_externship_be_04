from .admin_recruitment import urlpatterns as admin_patterns
from .recruitment_bookmarks import urlpatterns as bookmarks_patterns
from .tags import urlpatterns as tags_patterns

urlpatterns = bookmarks_patterns + tags_patterns + admin_patterns
