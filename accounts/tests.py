from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Profile


class RegisterTests(APITestCase):
    def test_register_creates_user_and_profile(self):
        r = self.client.post(
            "/api/auth/register/",
            {"username": "newuser", "email": "n@e.ru", "password": "pass12345"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data["username"], "newuser")
        self.assertEqual(r.data["role"], Profile.ROLE_GUEST)
        user = User.objects.get(username="newuser")
        self.assertTrue(hasattr(user, "profile"))

    def test_register_duplicate_username(self):
        User.objects.create_user(username="dup", password="pass12345")
        r = self.client.post(
            "/api/auth/register/",
            {"username": "dup", "password": "pass12345"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", r.data)


class LoginLogoutTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="pass12345")
        Profile.objects.create(user=self.user)

    def test_login_ok(self):
        r = self.client.post(
            "/api/auth/login/",
            {"username": "u", "password": "pass12345"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_login_wrong_password(self):
        r = self.client.post(
            "/api/auth/login/",
            {"username": "u", "password": "wrong"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_auth(self):
        r = self.client.get("/api/auth/me/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_ok(self):
        self.client.force_authenticate(self.user)
        r = self.client.get("/api/auth/me/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["username"], "u")