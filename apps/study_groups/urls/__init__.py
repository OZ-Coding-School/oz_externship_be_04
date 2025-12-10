from .note import urlpatterns as note_urlpatterns

urlpatterns = [
    *note_urlpatterns,
]

__all__ = ["urlpatterns"]
