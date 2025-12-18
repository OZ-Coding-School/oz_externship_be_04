from django.conf import settings
from django.conf.urls.static import static
from django.urls import URLPattern, URLResolver, include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns: list[URLPattern | URLResolver] = [
    path("api/v1", include("apps.lectures.urls")),
    path("api/v1", include("apps.lectures.urls.lecture_bookmark_url")),
    path("api/v1", include("apps.study_groups.urls")),
    path("api/v1/", include("apps.recruitment.urls")),
    path("api/v1/notifications", include("apps.notification.urls", "notification")),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/", include("apps.application.urls")),
    path("api/v1", include("apps.users.urls.admin_urls")),
    path("api/v1/", include("apps.chat.urls.v1")),
    path("api/v1/", include("apps.users.urls.account_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if "debug_toolbar" in settings.INSTALLED_APPS:
        urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
    if "drf_spectacular" in settings.INSTALLED_APPS:
        urlpatterns += [
            path("api/schema", SpectacularAPIView.as_view(), name="schema"),
            path("api/schema/swagger-ui", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
            path("api/schema/redoc", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
        ]
