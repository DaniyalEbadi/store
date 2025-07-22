from django.test import TestCase
from .models import members

class MembersModelTest(TestCase):
    def test_create_user(self):
        user = members.objects.create_user(
            username="testuser",
            password="plaintextpassword",
            email="test@example.com"
        )
        self.assertNotEqual(user.password, "plaintextpassword")
        self.assertTrue(user.check_password("plaintextpassword"))

    def test_create_superuser(self):
        superuser = members.objects.create_superuser(
            username="admin",
            password="adminpassword",
            email="admin@example.com"
        )
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
