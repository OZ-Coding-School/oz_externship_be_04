from __future__ import annotations

from typing import Optional

from rest_framework.exceptions import ValidationError

from apps.core.S3_constants import S3Constants

class S3FileValidator:
    """S3 파일 검증 클래스"""

    @staticmethod
    def validate_file_name(file_name: str) -> None:
        """파일 이름 검증"""
        if not file_name:
            raise ValidationError("유효하지 않은 파일명입니다.")
        if "." not in file_name or file_name.rsplit(".", 1)[0] == "":
            raise ValidationError("유효하지 않은 파일명입니다.")

    @staticmethod
    def validate_file_extension(file_name: str) -> str:
        """파일 확장자 검증 및 반환"""
        ext = file_name.rsplit(".", 1)[-1].lower()
        if ext not in S3Constants.get_all_allowed_extensions():
            raise ValidationError("허용된 확장자만 등록 가능합니다.")
        return ext

    @staticmethod
    def validate_content_type(content_type: Optional[str]) -> None:
        """Content-Type 검증"""
        if not content_type:
            raise ValidationError("유효한 Content-Type이 필요합니다.")

        if content_type not in S3Constants.get_all_mime_types():
            raise ValidationError("허용된 확장자(MIME)만 등록 가능합니다.")

    @staticmethod
    def validate_mime_match(ext: str, content_type: Optional[str]) -> None:
        """MIME 타입과 확장자 일치 검증"""
        if not content_type:
            raise ValidationError("유효한 Content-Type이 필요합니다.")

        if ext in S3Constants.IMAGE_MIME_BY_EXT:
            if content_type not in S3Constants.IMAGE_MIME_BY_EXT[ext]:
                raise ValidationError("허용된 이미지 확장자/형식만 등록 가능합니다.")
            return

        if ext in S3Constants.ATTACHMENT_MIME_BY_EXT:
            if content_type not in S3Constants.ATTACHMENT_MIME_BY_EXT[ext]:
                raise ValidationError("허용된 첨부파일 확장자/형식만 등록 가능합니다.")
            return

        raise ValidationError("허용된 확장자만 등록 가능합니다.")

    @staticmethod
    def validate_file_size(file_size: Optional[int]) -> None:
        """파일 크기 검증"""
        if file_size is None:
            raise ValidationError("파일 크기를 확인할 수 없습니다.")
        if file_size > S3Constants.MAX_FILE_SIZE_BYTES:
            raise ValidationError(f"{S3Constants.MAX_FILE_SIZE_MB}MB 이하만 업로드 가능합니다.")
