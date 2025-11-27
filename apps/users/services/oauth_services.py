import random
import string
from apps.users.models.users import User, SocialAccount


def generate_random_suffix(length=4):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


class SocialLoginService:

    @staticmethod
    def get_or_create_user(provider, provider_id, nickname, profile_img_url):
        try:
            account = SocialAccount.objects.get(provider=provider, provider_id=provider_id)
            return account.user, False  # 신규 아님
        except SocialAccount.DoesNotExist:
            pass

        base_nickname = nickname or f"user_{provider_id}"
        new_nickname = base_nickname
        while User.objects.filter(nickname=new_nickname).exists():
            new_nickname = f"{base_nickname}_{generate_random_suffix()}"

        dummy_email = f"{provider_id}@{provider}.social"

        user = User.objects.create(
            email=dummy_email,
            nickname=new_nickname,
            profile_img_url=profile_img_url,
            is_active=True,
        )

        SocialAccount.objects.create(
            user=user,
            provider=provider,
            provider_id=str(provider_id),
        )

        return user, True
