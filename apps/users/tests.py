from django.test import TransactionTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.chrome.webdriver import WebDriver
from .models import User


class CustomUserManagerTest(TransactionTestCase):
    def test_create_user(self):
        new_user = User.objects.create_user(email="test@user.com")
        user = User.objects.first()
        assert new_user == user

    def test_create_superuser(self):
        params = {
            "email": "test@superuser.com",
            "first_name": "John",
            "last_name": "Snow",
            "password": "test_password",
        }
        new_superuser = User.objects.create_superuser(**params)
        user = User.objects.first()
        assert new_superuser == user
        assert user.is_superuser
        assert user.first_name == "John"
        assert user.last_name == "Snow"


class UserLoginTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_login(self):
        User.objects.create_superuser(
            username="myuser", password="secret", email="myuser@example.com"
        )
        self.selenium.get("%s%s" % (self.live_server_url, "/users/login/"))
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys("myuser@example.com")
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys("secret")
        login_button = self.selenium.find_element_by_xpath('//input[@value="login"]')
        login_button.click()

        assert "you are logged in" in self.selenium.page_source

    def test_bad_login(self):
        User.objects.create_superuser(
            username="myuser", password="secret", email="myuser@example.com"
        )
        self.selenium.get("%s%s" % (self.live_server_url, "/users/login/"))
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys("myuser@example.com")
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys("wrongsecret")
        login_button = self.selenium.find_element_by_xpath('//input[@value="login"]')
        login_button.click()

        assert "you are logged in" not in self.selenium.page_source

    def test_logout(self):
        User.objects.create_superuser(
            username="myuser", password="secret", email="myuser@example.com"
        )
        self.selenium.get("%s%s" % (self.live_server_url, "/users/login/"))
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys("myuser@example.com")
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys("secret")
        login_button = self.selenium.find_element_by_xpath('//input[@value="login"]')
        login_button.click()

        self.selenium.get("%s%s" % (self.live_server_url, "/users/logout/"))

        assert "Logged out!" in self.selenium.page_source

        self.selenium.get("%s%s" % (self.live_server_url, "/"))

        assert "you are not logged in" in self.selenium.page_source
