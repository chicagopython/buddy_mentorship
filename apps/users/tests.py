from django.test import TransactionTestCase, TestCase, Client
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.conf import settings
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from .models import User
from .views import user_can_access_request

from buddy_mentorship.models import BuddyRequest, Profile, Skill, Experience
from buddy_mentorship.tests import create_test_users

import platform


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

        assert "Logout</a>" in self.selenium.page_source

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

        assert "Login</a>" in self.selenium.page_source

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

        assert "Login</a>" in self.selenium.page_source


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
            requestee=requestee,
            requestor=requestor,
            message="test message",
            request_type=BuddyRequest.RequestType.REQUEST,
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
    def setUp(self):
        skill = Skill.objects.create(skill="python")
        requestee = create_test_users(
            1,
            "requestee",
            [{"skill": skill, "level": 4, "exp_type": Experience.Type.CAN_HELP}],
        )[0]
        requestor = create_test_users(
            1,
            "requestor",
            [{"skill": skill, "level": 1, "exp_type": Experience.Type.WANT_HELP}],
        )[0]
        BuddyRequest.objects.create(
            requestee=requestee,
            requestor=requestor,
            message="test message",
            request_type=BuddyRequest.RequestType.REQUEST,
        )
        someone = create_test_users(1, "someone", [])[0]

    def test_invalid_request(self):
        someone = User.objects.get(email="someone0@buddy.com")
        c = Client()
        c.force_login(someone)
        buddy_request_id = BuddyRequest.objects.first().id
        response = c.get(f"/requests/{buddy_request_id + 1}")
        assert response.status_code == 404

    def test_no_access(self):
        someone = User.objects.get(email="someone0@buddy.com")
        c = Client()
        c.force_login(someone)
        buddy_request_id = BuddyRequest.objects.first().id
        response = c.get(f"/requests/{buddy_request_id}")
        assert response.status_code == 403

    def test_valid_request(self):
        requestee = User.objects.get(email="requestee0@buddy.com")
        requestor = User.objects.get(email="requestor0@buddy.com")
        c = Client()
        c.force_login(requestor)
        buddy_request_id = BuddyRequest.objects.first().id
        response = c.get(f"/requests/{buddy_request_id}")
        assert response.status_code == 200
        buddy_request = response.context["buddy_request"]
        assert buddy_request.requestee == requestee
        assert buddy_request.requestor == requestor
        assert buddy_request.message == "test message"


class RequestListTest(TestCase):
    def setUp(self):
        skill = Skill.objects.create(skill="python")
        create_test_users(
            1,
            "user",
            [{"skill": skill, "level": 3, "exp_type": Experience.Type.WANT_HELP}],
        )
        create_test_users(
            2,
            "requestee",
            [{"skill": skill, "level": 4, "exp_type": Experience.Type.CAN_HELP}],
        )
        create_test_users(
            2,
            "requestor",
            [{"skill": skill, "level": 2, "exp_type": Experience.Type.WANT_HELP}],
        )[0]

    def test_not_logged_in(self):
        c = Client()
        response = c.get("/requests/")
        self.assertRedirects(response, "/login/?next=/requests/")

    def test_no_requests(self):
        user = User.objects.get(email="user0@buddy.com")
        c = Client()
        c.force_login(user)
        response = c.get("/requests/")
        assert response.status_code == 200
        assert not response.context["requests_sent"]
        assert not response.context["requests_received"]
        assert not response.context["offers_received"]
        assert not response.context["offers_sent"]

    def test_one_or_two_requests(self):
        user = User.objects.get(email="user0@buddy.com")

        sent_request_1 = BuddyRequest.objects.create(
            requestor=user,
            requestee=User.objects.get(email="requestee0@buddy.com"),
            request_type=BuddyRequest.RequestType.REQUEST,
        )
        recd_request_1 = BuddyRequest.objects.create(
            requestee=user,
            requestor=User.objects.get(email="requestor0@buddy.com"),
            request_type=BuddyRequest.RequestType.REQUEST,
        )

        sent_offer_1 = BuddyRequest.objects.create(
            requestor=user,
            requestee=User.objects.get(email="requestee0@buddy.com"),
            request_type=BuddyRequest.RequestType.OFFER,
        )

        recd_offer_1 = BuddyRequest.objects.create(
            requestee=user,
            requestor=User.objects.get(email="requestor0@buddy.com"),
            request_type=BuddyRequest.RequestType.OFFER,
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
        assert recd_request_1 in requests_received

        offers_sent = response.context["offers_sent"]
        assert len(offers_sent) == 1
        assert sent_offer_1 in offers_sent

        offers_received = response.context["offers_received"]
        assert len(offers_received) == 1
        assert recd_offer_1 in offers_received

        # two requests in each category
        sent_request_2 = BuddyRequest.objects.create(
            requestor=user,
            requestee=User.objects.get(email="requestee1@buddy.com"),
            request_type=BuddyRequest.RequestType.REQUEST,
        )
        recd_request_2 = BuddyRequest.objects.create(
            requestee=user,
            requestor=User.objects.get(email="requestor1@buddy.com"),
            request_type=BuddyRequest.RequestType.REQUEST,
        )
        sent_offer_2 = BuddyRequest.objects.create(
            requestor=user,
            requestee=User.objects.get(email="requestee1@buddy.com"),
            request_type=BuddyRequest.RequestType.OFFER,
        )
        recd_offer_2 = BuddyRequest.objects.create(
            requestee=user,
            requestor=User.objects.get(email="requestor1@buddy.com"),
            request_type=BuddyRequest.RequestType.OFFER,
        )
        response = c.get("/requests/")
        assert response.status_code == 200

        requests_sent = response.context["requests_sent"]
        assert len(requests_sent) == 2
        assert sent_request_1 in requests_sent
        assert sent_request_2 in requests_sent

        requests_received = response.context["requests_received"]
        assert len(requests_received) == 2
        assert recd_request_1 in requests_received
        assert recd_request_2 in requests_received

        offers_sent = response.context["offers_sent"]
        assert len(offers_sent) == 2
        assert sent_offer_1 in offers_sent
        assert sent_offer_2 in offers_sent

        offers_received = response.context["offers_received"]
        assert len(offers_received) == 2
        assert recd_offer_1 in offers_received
        assert recd_offer_2 in offers_received

    def test_rejected_request(self):
        user = User.objects.get(email="user0@buddy.com")
        requestee = User.objects.get(email="requestee0@buddy.com")

        rejected_request = BuddyRequest.objects.create(
            requestor=user,
            requestee=requestee,
            request_type=BuddyRequest.RequestType.REQUEST,
        )

        rejected_request.status = BuddyRequest.Status.REJECTED
        rejected_request.save()

        rejected_offer = BuddyRequest.objects.create(
            requestor=user,
            requestee=requestee,
            request_type=BuddyRequest.RequestType.OFFER,
        )

        rejected_offer.status = BuddyRequest.Status.REJECTED
        rejected_offer.save()

        c = Client()
        c.force_login(user)
        response = c.get("/requests/")

        assert not response.context["requests_sent"]
        assert not response.context["offers_sent"]

        c.force_login(requestee)
        response = c.get("/requests/")

        assert not response.context["requests_received"]
        assert not response.context["offers_received"]
