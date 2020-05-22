from django.test import TransactionTestCase, TestCase, Client
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.conf import settings
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from .models import User
from .views import user_can_access_request

from buddy_mentorship.models import BuddyRequest, Profile

import platform

'''
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
        chrome_options = Options()
        if settings.CHROME_HEADLESS:
            chrome_options.add_argument("--headless")

        if not settings.CHROME_SANDBOX:
            chrome_options.add_argument("--no-sandbox")

        cls.selenium = WebDriver(chrome_options=chrome_options)
        cls.selenium.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_login(self):
        User.objects.create_superuser(
            username="myuser", password="secret", email="myuser@example.com"
        )
        self.selenium.get("%s%s" % (self.live_server_url, "/login/"))
        username_input = self.selenium.find_element(By.NAME, "username")
        username_input.send_keys("myuser@example.com")
        password_input = self.selenium.find_element(By.NAME, "password")
        password_input.send_keys("secret")
        login_button = self.selenium.find_element(By.XPATH, '//input[@value="login"]')
        login_button.click()

        assert "you are logged in" in self.selenium.page_source

    def test_bad_login(self):
        User.objects.create_superuser(
            username="myuser", password="secret", email="myuser@example.com"
        )
        self.selenium.get("%s%s" % (self.live_server_url, "/login/"))
        username_input = self.selenium.find_element(By.NAME, "username")
        username_input.send_keys("myuser@example.com")
        password_input = self.selenium.find_element(By.NAME, "password")
        password_input.send_keys("wrongsecret")
        login_button = self.selenium.find_element(By.XPATH, '//input[@value="login"]')
        login_button.click()

        assert "you are logged in" not in self.selenium.page_source

    def test_logout(self):
        User.objects.create_superuser(
            username="myuser", password="secret", email="myuser@example.com"
        )
        self.selenium.get("%s%s" % (self.live_server_url, "/login/"))
        username_input = self.selenium.find_element(By.NAME, "username")
        username_input.send_keys("myuser@example.com")
        password_input = self.selenium.find_element(By.NAME, "password")
        password_input.send_keys("secret")
        login_button = self.selenium.find_element(By.XPATH, '//input[@value="login"]')
        login_button.click()

        self.selenium.get("%s%s" % (self.live_server_url, "/logout/"))

        assert "Logged out!" in self.selenium.page_source

        self.selenium.get("%s%s" % (self.live_server_url, "/"))

        assert "you are not logged in" in self.selenium.page_source


class UserCanAccessRequestTest(TestCase):
    def test_user_can_access(self):
        params = {
            "email": "test@superuser.com",
            "first_name": "Sansa",
            "last_name": "Stark",
            "password": "test_password",
        }
        su = User.objects.create_superuser(**params)
        requestee = User.objects.create_user(email="requestee@user.com")
        Profile.objects.create(user=requestee)
        requestor = User.objects.create_user(email="requestor@user.com")
        Profile.objects.create(user=requestor)
        someone = User.objects.create_user(email="someone@user.com")
        buddy_request = BuddyRequest.objects.create(
            requestee=requestee, requestor=requestor, message="test message"
        )
        assert user_can_access_request(su, buddy_request)
        assert user_can_access_request(requestee, buddy_request)
        assert user_can_access_request(requestor, buddy_request)
        assert not user_can_access_request(someone, buddy_request)

        su.is_active = False
        su.save()
        requestee.is_active = False
        requestee.save()
        requestor.is_active = False
        requestor.save()
        assert not user_can_access_request(su, buddy_request)
        assert not user_can_access_request(requestee, buddy_request)
        assert not user_can_access_request(requestor, buddy_request)


class RequestDetailTest(TestCase):
    def setup(self):
        requestee = User.objects.create_user(email="requestee@user.com")
        requestor = User.objects.create_user(email="requestor@user.com")
        BuddyRequest.objects.create(
            requestee=requestee, requestor=requestor, message="test message"
        )

    def invalid_request(self):
        c = Client()
        response = c.get("/requests/2/")
        assert response.status_code == 404

    def no_access(self):
        someone = User.objects.create_user(email="someone@user.com")
        c = Client()
        c.force_login(someone)
        response = c.get("/requests/1/")
        assert response.status_code == 403

    def valid_request(self):
        requestee = User.objects.get(email="requestor@user.com")
        requestor = User.objects.get(email="requestor@user.com")
        c = Client()
        c.force_login(requestor)
        response = c.get("/requests/1/")
        assert response.status_code == 200
        buddy_request = response.context["buddy_request"]
        assert buddy_request.requestee == requestee
        assert buddy_request.requestor == requestor
        assert buddy_request.message == "test message"
        assert buddy_request.id == 1


class RequestListTest(TestCase):
    def setup(self):
        User.objects.create_user(email="user@user.com")

    def not_logged_in(self):
        c = Client()
        response = c.get("/requests/")
        self.assertRedirects(response, "/login/")

    def no_requests(self):
        user = User.objects.get(email="user@user.com")
        c = Client()
        c.force_login(user)
        response = c.get("/requests/")
        assert response.status_code == 200
        assert not response.context["requests_sent"]
        assert not response.context["requests_received"]

    def one_or_two_request(self):
        user = User.objects.get(email="user@user.com")

        sent_request_1 = BuddyRequest.objects.create(
            requestor=user,
            requestee=User.objects.create_user(email="requestee1@user.com"),
        )
        recd_request_1 = BuddyRequest.objects.create(
            requestee=user,
            requestor=User.objects.create_user(email="requestor1@user.com"),
        )

        # one request in each category
        c = Client()
        c.force_login(user)
        response = c.get("/requests/")
        assert response.status_code == 200

        requests_sent = response.context["requests_sent"]
        assert len(requests_sent) == 1
        assert sent_request_1 in requests_sent

        requests_received = response.context["requests_received"]
        assert len(requests_received) == 1
        assert recd_request_1 in requests_sent

        # two requests in each category
        sent_request_2 = BuddyRequest.objects.create(
            requestor=user,
            requestee=User.objects.create_user(email="requestee2@user.com"),
        )
        recd_request_2 = BuddyRequest.objects.create(
            requestee=user,
            requestor=User.objects.create_user(email="requestor2@user.com"),
        )
        response = c.get("/requests/")
        assert response.status_code == 200

        requests_sent = response.context["requests_sent"]
        assert len(requests_sent) == 2
        assert sent_request_1 in requests_sent
        assert sent_request_2 in requests_sent

        requests_received = response.context["requests_received"]
        assert len(requests_received) == 2
        assert recd_request_1 in requests_sent
        assert recd_request_2 in requests_sent
'''