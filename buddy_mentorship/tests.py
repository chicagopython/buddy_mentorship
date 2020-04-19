import datetime as dt

from django.test import TransactionTestCase, TestCase, Client
from django.utils import timezone

from .models import BuddyRequest, Profile
from .views import can_request, send_request

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


# very in progress
class SearchTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            email="elizabeth@bennet.org",
            first_name="Elizabeth",
            last_name="Bennet",
        )

        Profile.objects.create(
            user=user,
            bio="",
            can_help = True,
            want_help = True
        )

        mentor_one_skill = User.objects.create_user(
            email="mr@bennet.org",
            first_name="Mr.",
            last_name="Bennet",
        )

        Profile.objects.create(
            user=mentor_one_skill,
            bio="")


        mentor_another_skill = User.objects.create_user(
            email="jane@bennet.org",
            first_name="Jane",
            last_name="Bennet"
        )

        not_a_mentor = User.objects.create_user(
            email="jenny@bennet.org",
            first_name="Jane Gardiner",
            last_name"Bennet",
        )

        mentor_wrong_location = User.objects.create_user(
            email="mrs@gardiner.org",
            first_name="Mrs.",
            last_name="Gardiner"
        )

        mentor_wrong_skill = User.objects.create_user(
            email="charlotte@collins.org",
            first_name="Charlotte",
            last_name="Collins"
        )

        mentor_insufficient_skill = User.objects.create_user(
            email="lydia@bennet.org",
            first_name="Lydia",
            last_name="Bennet"
        )

        mentor_wrong_demo = User.objects.create_user(
            email="charles@bingley.org",
            first_name="Charles",
            last_name="Bingley"
        )

    def test_all_qualified(self):
        c = Client()
        response = c.get('/search/')
        search_results = response.queryset
        
