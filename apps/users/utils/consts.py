from django.db import models


class WithdrawalReason(models.TextChoices):
    NO_LONGER_NEEDED = "NO_LONGER_NEEDED", "서비스 이용할 시간이 없음"
    LACK_OF_INTEREST = "LACK_OF_INTEREST", "관심이 사라짐"
    TOO_DIFFICULT = "TOO_DIFFICULT", "서비스를 이용하기가 너무 어려움"
    FOUND_BETTER_SERVICE = "FOUND_BETTER_SERVICE", "더 좋은 대안을 찾음"
    PRIVACY_CONCERNS = "PRIVACY_CONCERNS", "개인정보/보안 우려"
    POOR_SERVICE_QUALITY = "POOR_SERVICE_QUALITY", "서비스 품질 불만"
    TECHNICAL_ISSUES = "TECHNICAL_ISSUES", "기술적 문제(버그 등)"
    LACK_OF_CONTENT = "LACK_OF_CONTENT", "원하는 콘텐츠나 기능의 부족"
    OTHER = "OTHER", "기타"


EMAiL_TEMPLATES = {
    "signup": {
        "subject": "[STUDY HUB] 회원가입 이메일 인증",
        "message": "[STUDY HUB] 본인확인 인증코드 {code} 5분 내에 입력해주세요 타인에게 절대 양도하지 마세요.",
    },
    "reset_password": {
        "subject": "[STUDY HUB] 비밀번호 재설정 이메일 인증",
        "message": "[STUDY HUB] 본인확인 인증코드 {code} 5분 내에 입력해주세요 타인에게 절대 양도하지 마세요.",
    },
    "restore": {
        "subject": "[STUDY HUB] 계정 복구 이메일 인증",
        "message": "[STUDY HUB] 본인확인 인증코드 {code} 5분 내에 입력해주세요 타인에게 절대 양도하지 마세요.",
    },
}
EMAiL_VERIFY_MESSAGE = {
    "signup": "[STUDY HUB] 회원가입을 위한 이메일 인증에 성공하였습니다.",
    "find_password": "[STUDY HUB] 비밀번호 찾기를 위한 이메일 인증에 성공하였습니다.",
    "restore": "[STUDY HUB] 계정복구를 위한 이메일 인증에 성공하였습니다.",
}

EMAIL_SEND_MESSAGE = {
    "signup": "[STUDY HUB] 회원가입 인증 코드",
    "find_password": "[STUDY HUB]비밀번호 찾기 인증 코드",
    "restore": "[STUDY HUB] 계정 복구 인증 코드",
}

SMS_SEND_MESSAGE = {
    "signup": "[STUDY HUB] 회원가입을 위한 휴대폰 인증 코드가 전송되었습니다.",
    "reset_password": "[STUDY HUB] 비밀번호 재설정을 위한 휴대폰 인증 코드가 전송되었습니다.",
    "find_email": "[STUDY HUB] 계정찾기를 위한 휴대폰 인증 코드가 전송되었습니다.",
    "change_phone": "[STUDY HUB] 휴대폰 번호 변경을 위한 휴대폰 인증 코드가 전송되었습니다.",
}
SMS_VERIFY_MESSAGE = {
    "signup": "[STUDY HUB] 회원가입을 위한 휴대폰 인증에 성공하였습니다.",
    "reset_password": "[STUDY HUB] 비밀번호 재설정을 위한 휴대폰 인증에 성공하였습니다.",
    "find_email": "[STUDY HUB] 계정찾기를 위한 휴대폰 인증에 성공하였습니다.",
    "change_phone": "[STUDY HUB] 휴대폰 번호 변경을 위한 휴대폰 인증에 성공하였습니다.",
}
