from django.test import TestCase, Client
from django.urls import reverse

from apps.users.models.users import User
from apps.users.models.social_user import SocialUser, ProviderChoices

PROVIDER = ProviderChoices.KAKAO.value

class SocialLoginAPITest(TestCase):

    def setUp(self) -> None:
        self.client = Client()
        self.url = reverse("social_login")

    def test_social_login_new_user(self) -> None:
        payload = {
            "provider": PROVIDER,
            "provider_id": "12345",
            "email": "test@example.com",
            "nickname": "tester",
        }

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_new_user"])

        user = User.objects.get(email="test@example.com")
        social = SocialUser.objects.get(user=user)

        self.assertEqual(social.provider, PROVIDER)
        self.assertEqual(social.provider_id, "12345")

    def test_social_login_existing_social_user(self) -> None:
        user = User.objects.create(
            email="old@example.com",
            nickname="old",
            name="old",
        )

        SocialUser.objects.create(
            user=user,
            provider=PROVIDER,
            provider_id="999",
        )

        payload = {
            "provider": PROVIDER,
            "provider_id": "999",
        }

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_new_user"])

    def test_social_login_existing_email_attaches_social(self) -> None:
        user = User.objects.create(
            email="mail@ex.com",
            nickname="base",
            name="base",
        )

        payload = {
            "provider": PROVIDER,
            "provider_id": "777",
            "email": "mail@ex.com",
            "nickname": "newnick",
        }

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 200)

        user.refresh_from_db()
        self.assertEqual(user.nickname, "newnick")

        social = SocialUser.objects.get(user=user)
        self.assertEqual(social.provider_id, "777")

    def test_nickname_collision(self) -> None:
        User.objects.create(
            email="a@a.com",
            nickname="tester",
            name="tester",
        )

        payload = {
            "provider": PROVIDER,
            "provider_id": "321",
            "nickname": "tester",
            "phone_number": "01099998888",
            "gender": "M",
            "profile_img_url": "https://example.com/profile.png",
        }

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 200)

        new_user = User.objects.get(id=response.json()["user_id"])
        self.assertTrue(new_user.nickname.startswith("tester_"))
