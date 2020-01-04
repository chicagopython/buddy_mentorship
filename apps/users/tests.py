from django.test import TransactionTestCase
from .models import User


class CustomUserManagerTest(TransactionTestCase):
    def test_create_user(self):
        new_user = User.objects.create_user(email="test@user.com")
        user = User.objects.first()
        assert new_user == user

    def test_create_superuser(self):
        params = {
            "email": "test@superuser.com",
            "password": "test_password"
        }
        new_superuser = User.objects.create_superuser(**params)
        user = User.objects.first()
        assert new_superuser == user
        assert user.is_superuser
