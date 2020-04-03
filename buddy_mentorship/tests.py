import datetime as dt

from django.test import TransactionTestCase, TestCase, Client
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils import timezone

from .models import BuddyRequest, Profile
from .views import can_request, send_request

from apps.users.views import user_can_access_request, request_detail
from apps.users.models import User

class CreateBuddyRequestTest(TransactionTestCase):
    def test_create_buddy_request(self):
        mentee = User.objects.create_user(email="mentee@user.com")
        mentor = User.objects.create_user(email="mentor@user.com")
        msg = "test message"
        new_buddy_request = BuddyRequest.objects.create(
            requestor=mentee, requestee=mentor, message=msg
        )
        buddy_request = BuddyRequest.objects.first()
        assert new_buddy_request == buddy_request
        assert timezone.now() - buddy_request.request_sent > dt.timedelta(seconds=0)
        assert timezone.now() - buddy_request.request_sent < dt.timedelta(minutes=1)
        assert buddy_request.requestee == mentor
        assert buddy_request.requestor == mentee
        assert buddy_request.message == msg
        assert buddy_request.__str__() == (
            f"Buddy request from mentee@user.com to mentor@user.com "
            f"on {buddy_request.request_sent.__str__()}"
        )


class ProfileTest(TestCase):
    def test_create_profile(self):
        new_user = User.objects.create_user(email="testprofile@user.com")
        user = User.objects.first()
        Profile.objects.create(user = user, bio="i'm super interested in Python", help_wanted = True, can_help = False)
        record = Profile.objects.get(id=1)
        self.assertEqual(record.user, user) 
        self.assertEqual(record.bio, "i'm super interested in Python")
        self.assertEqual(record.help_wanted, True)
        self.assertEqual(record.can_help, False)


class SendRequestTest(TestCase):
    def setUp(self):
        mentor = User.objects.create_user(
            first_name = "Frank",
            last_name = "Mackey",
            email="mentor@user.com"
        )

        Profile.objects.create(
            user=mentor, 
            bio="Experienced Undercover detective.",
            can_help=True,
            help_wanted=False
        )

        mentee = User.objects.create_user(
            first_name = "Cassie",
            last_name = "Maddox",
            email="mentee@user.com"
        )

        Profile.objects.create(
            user=mentee, 
            bio="Aspiring Undercover detective with background in Murder.",
            can_help=False,
            help_wanted=True
        )

        someone = User.objects.create_user(
            first_name = "Rob",
            last_name = "Ryan",
            email="someone@user.com"
        )

        Profile.objects.create(
            user=someone, 
            bio="You ever see somebody ruin their own life?",
            can_help=False,
            help_wanted=False
        )

    def test_can_request(self):
        mentee = User.objects.get(email="mentee@user.com")
        mentor = User.objects.get(email="mentor@user.com")
        someone = User.objects.get(email="someone@user.com")
        assert can_request(mentee, mentor)
        
        mentor.is_active = False
        assert not can_request(mentee, mentor)
        mentor.is_active = True

        buddy_request = BuddyRequest.objects.create(
            requestor=mentee,
            requestee=mentor,
            message="Please help me!"
        )
        assert not can_request(mentee, someone)
        assert not can_request(someone, mentor)
        assert not can_request(mentee, mentor)
        buddy_request.delete()

    def test_send_request(self):
        c = Client()
        mentee = User.objects.get(email="mentee@user.com")
        mentor = User.objects.get(email="mentor@user.com")
        assert not BuddyRequest.objects.filter(requestor=mentee, requestee=mentor)
        
        c.force_login(mentee)
        response = c.get(f"/send_request/{mentor.uuid}")
        assert response.status_code == 302
        assert BuddyRequest.objects.get(requestor=mentee)

        response = c.get(f"/send_request/{mentor.uuid}")
        assert response.status_code == 403
        assert len(BuddyRequest.objects.filter(requestor=mentee, requestee=mentor))==1
        
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
        requestor = User.objects.create_user(email="requestor@user.com")
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


class RequestControllerTest(TestCase):
    def setup(self):
        requestee = User.objects.create_user(email="requestee@user.com")
        requestor = User.objects.create_user(email="requestor@user.com")
        someone = User.objects.create_user(email="someone@user.com")
        buddy_request = BuddyRequest.objects.create(
            requestee=requestee, requestor=requestor, message="test message"
        )
    def invalid_request(self):
        pass
    def no_access(self):
        pass
    def valid_request(self):
        pass