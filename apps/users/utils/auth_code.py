import random
import uuid

from django.core.cache import cache

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


class AuthCodeCache(AuthCodeGenerator):

    @classmethod
    def save(cls, key: str, code: str, expires_time: int = 300) -> None:
        cache.set(key, code, expires_time)

    @classmethod
    def verify(cls, key: str, input_code: str) -> bool:
        get_code = cache.get(key)
        if not get_code:
            return False
        if get_code == input_code:
            cache.delete(key)
            return True
        else:
            return False
