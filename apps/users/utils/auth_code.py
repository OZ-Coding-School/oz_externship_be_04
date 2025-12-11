import random
import uuid
from apps.core.utils import base62


class AuthCodeGenerator:

    @classmethod
    def generate_mail_code(cls, length: int = 6) -> str:
        unique_mail_code = uuid.uuid4()
        auth_mail_code = base62.Base62.uuid_encode(unique_mail_code, length=length)
        return auth_mail_code

    @classmethod
    def generate_sms_code(cls) -> int:
        auth_sms_code = random.randint(100000, 999999)
        return auth_sms_code