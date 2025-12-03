from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.S3 import s3_uploader
from apps.core.S3_constants import FileType


class S3PresignedURLView(APIView):
    """S3 Presigned URL 발급 View"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="S3 Presigned URL 발급",
        description="프론트엔드가 S3에 직접 파일을 업로드하기 위한 Presigned URL을 발급합니다.",
        parameters=[
            OpenApiParameter(
                name="type",
                type=str,
                location="query",
                required=True,
                description="파일 타입",
                enum=[ft.value for ft in FileType],
            ),
            OpenApiParameter(
                name="content_type",
                type=str,
                location="query",
                required=True,
                description="MIME type (예: image/png, application/pdf)",
            ),
            OpenApiParameter(
                name="file_name",
                type=str,
                location="query",
                required=True,
                description="원본 파일명",
            ),
            OpenApiParameter(
                name="file_ext",
                type=str,
                location="query",
                required=True,
                description="파일 확장자 (예: png, pdf)",
            ),
        ],
        responses={
            200: {
                "description": "성공",
                "content": {
                    "application/json": {
                        "example": {
                            "upload_url": "https://study-hub.s3.ap-northeast-2.amazonaws.com/uploads/users/profiles/uuid.png?X-Amz-Algorithm=...",
                            "file_url": "https://study-hub.s3.ap-northeast-2.amazonaws.com/uploads/users/profiles/uuid.png",
                            "key": "uploads/users/profiles/uuid.png",
                            "headers": {"Content-Type": "image/png"},
                        }
                    }
                },
            },
            400: {
                "description": "잘못된 요청",
                "content": {
                    "application/json": {
                        "examples": {
                            "missing_params": {
                                "summary": "필수 파라미터 누락",
                                "value": {"error_detail": {"type": ["이 필드는 필수 항목입니다."]}},
                            },
                            "invalid_type": {
                                "summary": "유효하지 않은 파일 타입",
                                "value": {"error_detail": "유효하지 않은 파일 타입: INVALID_TYPE"},
                            },
                        }
                    }
                },
            },
            401: {
                "description": "인증 실패",
                "content": {
                    "application/json": {"example": {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."}}
                },
            },
        },
        tags=["Common"],
    )
    def get(self, request: Request) -> Response:

        file_type = request.query_params.get("type")
        content_type = request.query_params.get("content_type")
        file_name = request.query_params.get("file_name")
        file_ext = request.query_params.get("file_ext")

        required_params = {
            "type": file_type,
            "content_type": content_type,
            "file_name": file_name,
            "file_ext": file_ext,
        }

        missing_params = {key: ["이 필드는 필수 항목입니다."] for key, value in required_params.items() if not value}

        if missing_params:
            raise ValidationError(missing_params)

        result = s3_uploader.generate_presigned_url(
            file_type=file_type,
            content_type=content_type,
            file_name=file_name,
            file_ext=file_ext,
        )
        return Response(result, status=status.HTTP_200_OK)
