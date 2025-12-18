from __future__ import annotations

import logging
import uuid
from functools import lru_cache, wraps
from typing import Any, Callable

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    ParamValidationError,
)
from django.conf import settings
from rest_framework.exceptions import APIException, ValidationError

from apps.core.S3_constants import FileType, S3Constants
from apps.core.S3_validators import S3FileValidator

logger = logging.getLogger(__name__)


def handle_s3_errors(operation: str) -> Callable[..., Any]:
    """S3 작업 에러 핸들링 데코레이터"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except ValidationError:
                raise
            except APIException:
                raise
            except NoCredentialsError:
                logger.error("S3 credentials not found", exc_info=True)
                raise APIException("S3 자격 증명을 찾을 수 없습니다.")
            except ClientError as e:
                error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
                logger.error(f"S3 ClientError: {error_code}", exc_info=True)
                raise APIException(f"{operation} 중 오류가 발생했습니다: {error_code}")
            except ParamValidationError as e:
                logger.error("S3 ParamValidationError", exc_info=True)
                raise APIException(f"잘못된 파라미터입니다: {str(e)}")
            except BotoCoreError as e:
                logger.error("S3 BotoCoreError", exc_info=True)
                raise APIException(f"S3 연결 중 오류가 발생했습니다: {str(e)}")
            except Exception as e:
                logger.error("S3 Unexpected Error", exc_info=True)
                raise APIException(f"예상치 못한 오류가 발생했습니다: {str(e)}")

        return wrapper

    return decorator


class S3Uploader:
    """
    공통 S3 업로더 클래스 (boto3 기반)
    - boto3 클라이언트 생성
    - Presigned URL 생성 (POST/PUT)
    - 단일 / 복수 객체 삭제
    - 파일 업로드 (테스트 및 관리용)
    """

    @staticmethod
    @lru_cache(maxsize=1)
    def get_s3_client() -> Any:
        """S3 클라이언트 반환 (thread-safe lazy initialization)"""
        return boto3.client(
            "s3",
            aws_access_key_id=getattr(settings, "AWS_S3_ACCESS_KEY_ID", None),
            aws_secret_access_key=getattr(settings, "AWS_S3_SECRET_ACCESS_KEY", None),
            region_name=getattr(settings, "AWS_S3_REGION", None),
        )

    @classmethod
    def get_bucket_name(cls) -> str:
        """S3 버킷 이름 반환"""
        return getattr(settings, "AWS_S3_BUCKET_NAME", "")

    @classmethod
    def get_s3_base_url(cls) -> str:
        """S3 Base URL 반환"""
        bucket = cls.get_bucket_name()
        region = getattr(settings, "AWS_S3_REGION", "")
        return f"https://{bucket}.s3.{region}.amazonaws.com/"

    @classmethod
    @handle_s3_errors("Presigned URL 생성")
    def generate_presigned_url(
        cls,
        file_type: str,
        content_type: str,
        file_name: str,
        file_ext: str,
    ) -> dict[str, Any]:
        """
        Presigned URL 생성 (PUT 방식, 단건)

        Args:
            file_type: FileType enum 값
            content_type: MIME type
            file_name: 원본 파일명
            file_ext: 파일 확장자

        Returns:
            dict: Presigned URL 정보
                - upload_url: Presigned URL (쿼리스트링 포함)
                - file_url: 실제 파일 URL (쿼리스트링 제외)
                - key: S3 객체 키
                - headers: 업로드 시 필요한 헤더

        Raises:
            ValidationError: 파일 타입, 파일명, 확장자, MIME 타입 검증 실패
            APIException: Presigned URL 생성 실패
        """

        try:
            file_type_enum = FileType(file_type)
        except ValueError:
            raise ValidationError(f"유효하지 않은 파일 타입: {file_type}")

        S3FileValidator.validate_file_name(file_name)

        ext = S3FileValidator.validate_extension_match(file_name, file_ext)

        S3FileValidator.validate_content_type(content_type)

        S3FileValidator.validate_mime_match(ext, content_type)

        prefix = S3Constants.PATH_MAPPING.get(file_type_enum)
        if not prefix:
            raise ValidationError(f"경로를 찾을 수 없습니다: {file_type}")

        key = f"{prefix}/{uuid.uuid4()}.{ext}"

        upload_url = cls.get_s3_client().generate_presigned_url(
            "put_object",
            Params={
                "Bucket": cls.get_bucket_name(),
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=S3Constants.PRESIGNED_URL_EXPIRE_SECONDS,
        )

        return {
            "upload_url": upload_url,
            "file_url": f"{cls.get_s3_base_url()}{key}",
            "key": key,
            "headers": {"Content-Type": content_type},
        }

    @classmethod
    @handle_s3_errors("파일 삭제")
    def delete_file(cls, key: str) -> dict[str, Any]:
        """
        S3 파일 삭제 (단일)

        Args:
            key: S3 객체 키 (예: uploads/recruitments/images/uuid.png)

        Returns:
            dict: 삭제 결과
                - message: 성공 메시지
                - key: 삭제된 객체 키

        Raises:
            ValidationError: key가 비어있을 경우
            APIException: S3 삭제 실패
        """
        if not key or not key.strip():
            raise ValidationError("key는 필수입니다.")

        cls.get_s3_client().delete_object(
            Bucket=cls.get_bucket_name(),
            Key=key,
        )

        return {
            "message": "파일이 성공적으로 삭제되었습니다.",
            "key": key,
        }


s3_uploader = S3Uploader()
