from django.urls import path

from .S3_view import S3PresignedURLView

app_name = "core"

urlpatterns = [
    path("s3-presigned-url", S3PresignedURLView.as_view(), name="s3-presigned-url"),
]
