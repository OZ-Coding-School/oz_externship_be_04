from __future__ import annotations

import logging
import uuid
from functools import wraps
from typing import Any, Callable, ClassVar, cast

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    ParamValidationError,
)
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
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

    _s3_client: Any = None

    @classmethod
    def get_s3_client(cls) -> Any:
        """S3 클라이언트 반환 (lazy initialization)"""
        if cls._s3_client is None:
            cls._s3_client = boto3.client(
                "s3",
                aws_access_key_id=getattr(settings, "AWS_S3_ACCESS_KEY_ID", None),
                aws_secret_access_key=getattr(settings, "AWS_S3_SECRET_ACCESS_KEY", None),
                region_name=getattr(settings, "AWS_S3_REGION", None),
            )
        return cls._s3_client

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
    def generate_presigned_urls(cls, prefix: str, files: list[dict[str, str]]) -> list[dict[str, Any]]:
        """
        Presigned URL 생성 (POST 방식, 복수)

        Args:
            prefix: S3 저장 경로 prefix
            files: 파일 정보 리스트 (file_name, content_type 포함)

        Returns:
            list[dict]: Presigned URL 정보 리스트

        Raises:
            APIException: Presigned URL 생성 실패
        """
        presigned_data: list[dict[str, Any]] = []

        if prefix and not prefix.endswith("/"):
            prefix += "/"

        for file in files:
            file_name = file.get("file_name")
            content_type = file.get("content_type")

            if not file_name or not content_type:
                raise ValidationError("file_name과 content_type은 필수입니다.")

            S3FileValidator.validate_file_name(file_name)
            ext = S3FileValidator.validate_file_extension(file_name)
            S3FileValidator.validate_content_type(content_type)
            S3FileValidator.validate_mime_match(ext, content_type)

            key = f"{prefix}{uuid.uuid4()}_{file_name}"

            presigned_post = cls.get_s3_client().generate_presigned_post(
                Bucket=cls.get_bucket_name(),
                Key=key,
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                    [
                        "content-length-range",
                        S3Constants.MIN_FILE_SIZE_BYTES,
                        S3Constants.MAX_FILE_SIZE_BYTES,
                    ],
                ],
                ExpiresIn=S3Constants.PRESIGNED_URL_EXPIRE_SECONDS,
            )

            presigned_data.append(
                {
                    "file_name": file_name,
                    "key": key,
                    "url": presigned_post["url"],
                    "fields": presigned_post["fields"],
                    "file_url": cls.get_s3_base_url() + key,
                    "expires_in": S3Constants.PRESIGNED_URL_EXPIRE_SECONDS,
                }
            )

        return presigned_data

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

        S3FileValidator.validate_file_extension(file_name)

        S3FileValidator.validate_mime_match(file_ext, content_type)

        prefix = S3Constants.PATH_MAPPING.get(file_type_enum)
        if not prefix:
            raise ValidationError(f"경로를 찾을 수 없습니다: {file_type}")

        key = f"{prefix}/{uuid.uuid4()}.{file_ext}"

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

s3_uploader = S3Uploader()
