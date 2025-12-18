from __future__ import annotations

import logging
from typing import Any, Optional

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    ParamValidationError,
)
from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from moto import mock_aws
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.test import APIClient

from apps.core.S3 import S3Uploader
from apps.core.S3_constants import FileType, S3Constants
from apps.core.S3_validators import S3FileValidator
from apps.users.models import User


class S3FileValidatorTest(TestCase):
    """S3FileValidator 단위 테스트"""

    def test_validate_file_name_success(self) -> None:
        S3FileValidator.validate_file_name("test.png")
        S3FileValidator.validate_file_name("document.pdf")
        S3FileValidator.validate_file_name("my-file_123.jpg")

    def test_validate_file_name_empty(self) -> None:
        with self.assertRaises(ValidationError):
            S3FileValidator.validate_file_name("")

    def test_validate_file_name_no_extension(self) -> None:
        with self.assertRaises(ValidationError):
            S3FileValidator.validate_file_name("noextension")

    def test_validate_file_name_only_extension(self) -> None:
        with self.assertRaises(ValidationError):
            S3FileValidator.validate_file_name(".png")

    def test_validate_file_extension_images(self) -> None:
        self.assertEqual(S3FileValidator.validate_file_extension("test.png"), "png")
        self.assertEqual(S3FileValidator.validate_file_extension("test.JPG"), "jpg")
        self.assertEqual(S3FileValidator.validate_file_extension("test.jpeg"), "jpeg")
        self.assertEqual(S3FileValidator.validate_file_extension("test.gif"), "gif")
        self.assertEqual(S3FileValidator.validate_file_extension("test.webp"), "webp")

    def test_validate_file_extension_attachments(self) -> None:
        self.assertEqual(S3FileValidator.validate_file_extension("doc.pdf"), "pdf")
        self.assertEqual(S3FileValidator.validate_file_extension("doc.docx"), "docx")
        self.assertEqual(S3FileValidator.validate_file_extension("data.xlsx"), "xlsx")
        self.assertEqual(S3FileValidator.validate_file_extension("file.zip"), "zip")
        self.assertEqual(S3FileValidator.validate_file_extension("file.hwp"), "hwp")

    def test_validate_file_extension_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            S3FileValidator.validate_file_extension("malware.exe")
        with self.assertRaises(ValidationError):
            S3FileValidator.validate_file_extension("script.sh")

    def test_validate_content_type_success(self) -> None:
        S3FileValidator.validate_content_type("image/png")
        S3FileValidator.validate_content_type("application/pdf")
        S3FileValidator.validate_content_type("text/plain")

    def test_validate_content_type_none(self) -> None:
        with self.assertRaises(ValidationError):
            S3FileValidator.validate_content_type(None)

    def test_validate_content_type_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            S3FileValidator.validate_content_type("application/x-executable")

    def test_validate_mime_match_images(self) -> None:
        S3FileValidator.validate_mime_match("png", "image/png")
        S3FileValidator.validate_mime_match("jpg", "image/jpeg")
        S3FileValidator.validate_mime_match("jpeg", "image/jpeg")

    def test_validate_mime_match_attachments(self) -> None:
        S3FileValidator.validate_mime_match("pdf", "application/pdf")
        S3FileValidator.validate_mime_match(
            "docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        S3FileValidator.validate_mime_match("txt", "text/plain")

    def test_validate_mime_match_mismatch(self) -> None:
        with self.assertRaises(ValidationError):
            S3FileValidator.validate_mime_match("png", "application/pdf")
        with self.assertRaises(ValidationError):
            S3FileValidator.validate_mime_match("pdf", "image/png")

    def test_validate_extension_match_success(self) -> None:
        """파일명과 확장자 일치 검증 성공"""
        self.assertEqual(S3FileValidator.validate_extension_match("test.png", "png"), "png")
        self.assertEqual(S3FileValidator.validate_extension_match("test.PNG", "png"), "png")
        self.assertEqual(S3FileValidator.validate_extension_match("document.pdf", "pdf"), "pdf")
        self.assertEqual(S3FileValidator.validate_extension_match("data.xlsx", "xlsx"), "xlsx")
        self.assertEqual(S3FileValidator.validate_extension_match("file.hwp", "hwp"), "hwp")

    def test_validate_extension_match_mismatch(self) -> None:
        """파일명과 확장자 불일치"""
        with self.assertRaises(ValidationError) as ctx:
            S3FileValidator.validate_extension_match("test.png", "jpg")
        self.assertIn("확장자", str(ctx.exception.detail))

        with self.assertRaises(ValidationError):
            S3FileValidator.validate_extension_match("document.pdf", "docx")

        with self.assertRaises(ValidationError):
            S3FileValidator.validate_extension_match("image.png", "gif")

    def test_validate_extension_match_invalid_extension(self) -> None:
        """허용되지 않은 확장자 (file_name에서)"""
        with self.assertRaises(ValidationError):
            S3FileValidator.validate_extension_match("malware.exe", "exe")

        with self.assertRaises(ValidationError):
            S3FileValidator.validate_extension_match("script.sh", "sh")

    def test_validate_file_size_success(self) -> None:
        S3FileValidator.validate_file_size(1024)
        S3FileValidator.validate_file_size(5 * 1024 * 1024)
        S3FileValidator.validate_file_size(S3Constants.MAX_FILE_SIZE_BYTES)

    def test_validate_file_size_none(self) -> None:
        with self.assertRaises(ValidationError):
            S3FileValidator.validate_file_size(None)

    def test_validate_file_size_too_large(self) -> None:
        with self.assertRaises(ValidationError):
            S3FileValidator.validate_file_size(S3Constants.MAX_FILE_SIZE_BYTES + 1)


class S3ConstantsTest(TestCase):
    """S3Constants 단위 테스트"""

    def test_get_all_allowed_extensions(self) -> None:
        extensions = S3Constants.get_all_allowed_extensions()
        self.assertIn("png", extensions)
        self.assertIn("jpg", extensions)
        self.assertIn("pdf", extensions)
        self.assertIn("docx", extensions)
        self.assertGreater(len(extensions), 10)

    def test_get_all_mime_types(self) -> None:
        mimes = S3Constants.get_all_mime_types()
        self.assertIn("image/png", mimes)
        self.assertIn("image/jpeg", mimes)
        self.assertIn("application/pdf", mimes)
        self.assertGreater(len(mimes), 10)

    def test_path_mapping_complete(self) -> None:
        for file_type in FileType:
            self.assertIn(file_type, S3Constants.PATH_MAPPING)
            path = S3Constants.PATH_MAPPING[file_type]
            self.assertIsInstance(path, str)
            self.assertGreater(len(path), 0)

    def test_file_size_constants(self) -> None:
        self.assertEqual(S3Constants.MAX_FILE_SIZE_MB, 10)
        self.assertEqual(S3Constants.MAX_FILE_SIZE_BYTES, 10 * 1024 * 1024)
        self.assertEqual(S3Constants.MIN_FILE_SIZE_BYTES, 1)

    def test_presigned_url_expire(self) -> None:
        self.assertEqual(S3Constants.PRESIGNED_URL_EXPIRE_SECONDS, 300)


class S3MockTestBase(TestCase):
    """S3 Mock 테스트를 위한 Base 클래스"""

    _mock: Optional[Any] = None
    bucket: str
    region: str

    def setUp(self) -> None:
        """S3 Mock 환경 설정"""
        logging.disable(logging.CRITICAL)

        self._mock = mock_aws()
        self._mock.start()

        self.bucket = "test-bucket"
        self.region = "ap-northeast-2"

        setattr(settings, "AWS_S3_BUCKET_NAME", self.bucket)
        setattr(settings, "AWS_S3_REGION", self.region)
        setattr(settings, "AWS_S3_ACCESS_KEY_ID", "test-key")
        setattr(settings, "AWS_S3_SECRET_ACCESS_KEY", "test-secret")

        S3Uploader.get_s3_client.cache_clear()
        S3Uploader.get_s3_client().create_bucket(
            Bucket=self.bucket,
            CreateBucketConfiguration={"LocationConstraint": self.region},
        )

    def tearDown(self) -> None:
        """S3 Mock 환경 정리"""
        if self._mock is not None:
            self._mock.stop()
        S3Uploader.get_s3_client.cache_clear()
        logging.disable(logging.NOTSET)


class S3UploaderTest(S3MockTestBase):
    """S3Uploader 통합 테스트 (정상 케이스 + 에러 케이스)"""

    def test_lazy_initialization(self) -> None:
        """lazy initialization 및 캐싱 검증"""
        S3Uploader.get_s3_client.cache_clear()
        client1 = S3Uploader.get_s3_client()
        client2 = S3Uploader.get_s3_client()
        self.assertIs(client1, client2)

    def test_get_bucket_name(self) -> None:
        """버킷 이름 반환"""
        self.assertEqual(S3Uploader.get_bucket_name(), self.bucket)

    def test_get_s3_base_url(self) -> None:
        """S3 Base URL 반환"""
        url = S3Uploader.get_s3_base_url()
        self.assertTrue(url.startswith("https://"))
        self.assertIn(self.bucket, url)
        self.assertIn("s3.", url)

    def test_generate_presigned_url_success(self) -> None:
        """Presigned URL 생성 성공 (PUT 방식)"""
        result = S3Uploader.generate_presigned_url(
            file_type=FileType.USER_PROFILE_IMAGE.value,
            content_type="image/png",
            file_name="profile.png",
            file_ext="png",
        )

        self.assertIn("upload_url", result)
        self.assertIn("file_url", result)
        self.assertIn("key", result)
        self.assertIn("headers", result)
        self.assertEqual(result["headers"]["Content-Type"], "image/png")

    def test_generate_presigned_url_invalid_type(self) -> None:
        """잘못된 파일 타입"""
        with self.assertRaises(ValidationError):
            S3Uploader.generate_presigned_url(
                file_type="INVALID",
                content_type="image/png",
                file_name="test.png",
                file_ext="png",
            )

    def test_generate_presigned_url_mime_mismatch(self) -> None:
        """MIME 타입 불일치"""
        with self.assertRaises(ValidationError):
            S3Uploader.generate_presigned_url(
                file_type=FileType.USER_PROFILE_IMAGE.value,
                content_type="application/pdf",
                file_name="test.png",
                file_ext="png",
            )

    def test_generate_presigned_url_extension_mismatch(self) -> None:
        """파일명과 file_ext 파라미터 불일치"""
        with self.assertRaises(ValidationError) as ctx:
            S3Uploader.generate_presigned_url(
                file_type=FileType.USER_PROFILE_IMAGE.value,
                content_type="image/jpeg",
                file_name="test.png",
                file_ext="jpg",
            )
        self.assertIn("확장자", str(ctx.exception.detail))

    def test_generate_presigned_url_security_exploit_attempt(self) -> None:
        """보안: 악의적인 파일 업로드 시도"""
        with self.assertRaises(ValidationError) as ctx:
            S3Uploader.generate_presigned_url(
                file_type=FileType.NOTE_ATTACHMENT.value,
                content_type="application/pdf",
                file_name="malware.exe",
                file_ext="pdf",
            )

    def test_presigned_url_errors(self) -> None:
        """Presigned URL 생성 에러 핸들링 검증"""
        from unittest.mock import patch

        with patch.object(S3Uploader, "get_s3_client") as mock:
            mock.return_value.generate_presigned_url.side_effect = NoCredentialsError()
            with self.assertRaises(APIException) as ctx:
                S3Uploader.generate_presigned_url(FileType.USER_PROFILE_IMAGE.value, "image/png", "test.png", "png")
            self.assertIn("자격 증명", str(ctx.exception.detail))

        with patch.object(S3Uploader, "get_s3_client") as mock:
            error: Any = {"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}}
            mock.return_value.generate_presigned_url.side_effect = ClientError(error, "generate_presigned_url")
            with self.assertRaises(APIException) as ctx:
                S3Uploader.generate_presigned_url(FileType.USER_PROFILE_IMAGE.value, "image/png", "test.png", "png")
            self.assertIn("Presigned URL 생성 중", str(ctx.exception.detail))

        with patch.object(S3Uploader, "get_s3_client") as mock:
            mock.return_value.generate_presigned_url.side_effect = ParamValidationError(report="Invalid param")
            with self.assertRaises(APIException) as ctx:
                S3Uploader.generate_presigned_url(FileType.USER_PROFILE_IMAGE.value, "image/png", "test.png", "png")
            self.assertIn("잘못된 파라미터", str(ctx.exception.detail))

        with patch.object(S3Uploader, "get_s3_client") as mock:
            mock.return_value.generate_presigned_url.side_effect = BotoCoreError()
            with self.assertRaises(APIException) as ctx:
                S3Uploader.generate_presigned_url(FileType.USER_PROFILE_IMAGE.value, "image/png", "test.png", "png")
            self.assertIn("S3 연결 중", str(ctx.exception.detail))

        with patch.object(S3Uploader, "get_s3_client") as mock:
            mock.return_value.generate_presigned_url.side_effect = Exception("Unexpected error")
            with self.assertRaises(APIException) as ctx:
                S3Uploader.generate_presigned_url(FileType.USER_PROFILE_IMAGE.value, "image/png", "test.png", "png")
            self.assertIn("예상치 못한 오류", str(ctx.exception.detail))

    def test_delete_file_success(self) -> None:
        """단일 파일 삭제 성공"""
        key = "uploads/test/test-file.png"
        S3Uploader.get_s3_client().put_object(
            Bucket=self.bucket,
            Key=key,
            Body=b"test content",
        )

        result = S3Uploader.delete_file(key=key)

        self.assertEqual(result["message"], "파일이 성공적으로 삭제되었습니다.")
        self.assertEqual(result["key"], key)

        with self.assertRaises(ClientError):
            S3Uploader.get_s3_client().head_object(Bucket=self.bucket, Key=key)

    def test_delete_file_empty_key(self) -> None:
        """빈 key로 삭제 시도"""
        with self.assertRaises(ValidationError) as ctx:
            S3Uploader.delete_file(key="")
        self.assertIn("key는 필수입니다", str(ctx.exception.detail))

        with self.assertRaises(ValidationError) as ctx:
            S3Uploader.delete_file(key="   ")
        self.assertIn("key는 필수입니다", str(ctx.exception.detail))

    def test_delete_file_not_found(self) -> None:
        """존재하지 않는 파일 삭제 시도"""
        non_existent_key = "uploads/test/non-existent-file.png"

        with self.assertRaises(ValidationError) as ctx:
            S3Uploader.delete_file(key=non_existent_key)
        self.assertIn("파일이 존재하지 않습니다", str(ctx.exception.detail))

    def test_delete_file_errors(self) -> None:
        """파일 삭제 에러 핸들링"""
        from unittest.mock import patch

        with patch.object(S3Uploader, "get_s3_client") as mock:
            mock.return_value.delete_object.side_effect = NoCredentialsError()
            with self.assertRaises(APIException) as ctx:
                S3Uploader.delete_file(key="test/file.png")
            self.assertIn("자격 증명", str(ctx.exception.detail))

        with patch.object(S3Uploader, "get_s3_client") as mock:
            error: Any = {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}
            mock.return_value.delete_object.side_effect = ClientError(error, "delete_object")
            with self.assertRaises(APIException) as ctx:
                S3Uploader.delete_file(key="test/file.png")
            self.assertIn("파일 삭제 중", str(ctx.exception.detail))


class S3APITestBase(S3MockTestBase):
    """S3 API 테스트를 위한 Base 클래스 (인증된 사용자 포함)"""

    def setUp(self) -> None:
        super().setUp()
        self.client: Any = APIClient()
        self.user = User.objects.create(
            email="test@example.com",
            password="password123",
            name="테스트",
            nickname="tester",
            phone_number="01012345678",
            gender="M",
            birthday=timezone.now().date(),
            is_active=True,
        )


class S3PresignedURLViewTest(S3APITestBase):
    """S3 Presigned URL API 테스트"""

    def test_presigned_url_unauthenticated(self) -> None:
        """인증 없이 요청"""
        response = self.client.get(
            "/api/v1/s3-presigned-url",
            {
                "type": FileType.USER_PROFILE_IMAGE.value,
                "content_type": "image/png",
                "file_name": "test.png",
                "file_ext": "png",
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_presigned_url_success(self) -> None:
        """Presigned URL 발급 성공"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            "/api/v1/s3-presigned-url",
            {
                "type": FileType.USER_PROFILE_IMAGE.value,
                "content_type": "image/png",
                "file_name": "test.png",
                "file_ext": "png",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("upload_url", response.data)
        self.assertIn("file_url", response.data)
        self.assertIn("key", response.data)
        self.assertIn("headers", response.data)

    def test_presigned_url_missing_params(self) -> None:
        """필수 파라미터 누락"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/s3-presigned-url", {"type": FileType.USER_PROFILE_IMAGE.value})
        self.assertEqual(response.status_code, 400)

    def test_presigned_url_invalid_file_type(self) -> None:
        """유효하지 않은 파일 타입"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            "/api/v1/s3-presigned-url",
            {
                "type": "INVALID_TYPE",
                "content_type": "image/png",
                "file_name": "test.png",
                "file_ext": "png",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_presigned_url_invalid_extension(self) -> None:
        """허용되지 않은 확장자"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            "/api/v1/s3-presigned-url",
            {
                "type": FileType.USER_PROFILE_IMAGE.value,
                "content_type": "application/exe",
                "file_name": "test.exe",
                "file_ext": "exe",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_presigned_url_mime_mismatch(self) -> None:
        """MIME 타입과 확장자 불일치"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            "/api/v1/s3-presigned-url",
            {
                "type": FileType.USER_PROFILE_IMAGE.value,
                "content_type": "image/jpeg",
                "file_name": "test.png",
                "file_ext": "png",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_presigned_url_filename_ext_mismatch(self) -> None:
        """파일명과 file_ext 파라미터 불일치"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            "/api/v1/s3-presigned-url",
            {
                "type": FileType.USER_PROFILE_IMAGE.value,
                "content_type": "image/jpeg",
                "file_name": "profile.png",
                "file_ext": "jpg",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("확장자", str(response.data))

    def test_presigned_url_security_attack(self) -> None:
        """보안: 악의적인 파일 확장자 변조 시도"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            "/api/v1/s3-presigned-url",
            {
                "type": FileType.NOTE_ATTACHMENT.value,
                "content_type": "application/pdf",
                "file_name": "script.exe",
                "file_ext": "pdf",
            },
        )
        self.assertEqual(response.status_code, 400)


class S3FileDeleteViewTest(S3APITestBase):
    """S3 파일 삭제 API 테스트 (단일)"""

    def test_delete_file_unauthenticated(self) -> None:
        """인증 없이 삭제 요청"""
        response = self.client.delete(
            "/api/v1/s3-file",
            {"key": "uploads/test/file.png"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_delete_file_success(self) -> None:
        """파일 삭제 성공"""
        self.client.force_authenticate(user=self.user)
        key = "uploads/test/test-file.png"
        S3Uploader.get_s3_client().put_object(
            Bucket=self.bucket,
            Key=key,
            Body=b"test content",
        )

        response = self.client.delete(
            "/api/v1/s3-file",
            {"key": key},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["key"], key)

    def test_delete_file_missing_key(self) -> None:
        """key 파라미터 누락"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            "/api/v1/s3-file",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_delete_file_empty_key(self) -> None:
        """빈 key로 삭제 시도"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            "/api/v1/s3-file",
            {"key": ""},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
