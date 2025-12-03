from __future__ import annotations

from enum import Enum
from typing import ClassVar

from apps.core.constants import (
    RECRUITMENT_FILE_UPLOAD_PATH,
    RECRUITMENT_IMAGE_UPLOAD_PATH,
    STUDY_GROUP_IMAGE_UPLOAD_PATH,
    STUDY_NOTE_FILE_UPLOAD_PATH,
    STUDY_NOTE_IMAGE_UPLOAD_PATH,
    USER_PROFILE_IMAGE_UPLOAD_PATH,
)


class FileType(str, Enum):
    """파일 타입"""

    USER_PROFILE_IMAGE = "USER_PROFILE_IMAGE"
    STUDY_GROUP_IMAGE = "STUDY_GROUP_IMAGE"
    RECRUITMENT_IMAGE = "RECRUITMENT_IMAGE"
    NOTE_IMAGE = "NOTE_IMAGE"
    NOTE_ATTACHMENT = "NOTE_ATTACHMENT"
    RECRUITMENT_ATTACHMENT = "RECRUITMENT_ATTACHMENT"


class S3Constants:
    """S3 관련 상수 정의"""

    MAX_FILE_SIZE_MB: ClassVar[int] = 10
    MAX_FILE_SIZE_BYTES: ClassVar[int] = MAX_FILE_SIZE_MB * 1024 * 1024
    MIN_FILE_SIZE_BYTES: ClassVar[int] = 1

    PRESIGNED_URL_EXPIRE_SECONDS: ClassVar[int] = 300

    ALLOWED_IMAGE_EXTENSIONS: ClassVar[set[str]] = {
        "jpg",
        "jpeg",
        "png",
        "gif",
        "webp",
    }

    ALLOWED_ATTACHMENT_EXTENSIONS: ClassVar[set[str]] = {
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "txt",
        "md",
        "hwp",
        "zip",
    }

    IMAGE_MIME_BY_EXT: ClassVar[dict[str, set[str]]] = {
        "jpg": {"image/jpeg"},
        "jpeg": {"image/jpeg"},
        "png": {"image/png"},
        "gif": {"image/gif"},
        "webp": {"image/webp"},
    }

    ATTACHMENT_MIME_BY_EXT: ClassVar[dict[str, set[str]]] = {
        "pdf": {"application/pdf"},
        "doc": {"application/msword"},
        "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        "xls": {"application/vnd.ms-excel"},
        "xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
        "txt": {"text/plain"},
        "md": {"text/markdown", "text/x-markdown"},
        "hwp": {"application/x-hwp", "application/haansofthwp"},
        "zip": {"application/zip"},
    }

    PATH_MAPPING: ClassVar[dict[FileType, str]] = {
        FileType.USER_PROFILE_IMAGE: USER_PROFILE_IMAGE_UPLOAD_PATH.rstrip("/"),
        FileType.STUDY_GROUP_IMAGE: STUDY_GROUP_IMAGE_UPLOAD_PATH.rstrip("/"),
        FileType.RECRUITMENT_IMAGE: RECRUITMENT_IMAGE_UPLOAD_PATH.rstrip("/"),
        FileType.NOTE_IMAGE: STUDY_NOTE_IMAGE_UPLOAD_PATH.rstrip("/"),
        FileType.RECRUITMENT_ATTACHMENT: RECRUITMENT_FILE_UPLOAD_PATH.rstrip("/"),
        FileType.NOTE_ATTACHMENT: STUDY_NOTE_FILE_UPLOAD_PATH.rstrip("/"),
    }

    @classmethod
    def get_all_allowed_extensions(cls) -> set[str]:
        """모든 허용된 확장자 반환"""
        return cls.ALLOWED_IMAGE_EXTENSIONS | cls.ALLOWED_ATTACHMENT_EXTENSIONS

    @classmethod
    def get_all_mime_types(cls) -> set[str]:
        """모든 허용된 MIME 타입 반환"""
        all_mimes: set[str] = set()
        for mime_set in cls.IMAGE_MIME_BY_EXT.values():
            all_mimes.update(mime_set)
        for mime_set in cls.ATTACHMENT_MIME_BY_EXT.values():
            all_mimes.update(mime_set)
        return all_mimes
