from django.urls import path

from .S3_view import S3FileDeleteView, S3PresignedURLView

app_name = "core"

urlpatterns = [
    path("s3-presigned-url", S3PresignedURLView.as_view(), name="s3-presigned-url"),
    path("s3-file", S3FileDeleteView.as_view(), name="s3-file"),
]
