import datetime as dt

from django.test import TransactionTestCase, TestCase, Client
from django.utils import timezone
from django.utils.encoding import escape_uri_path

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
            can_help=True,
            help_wanted=True
        )

        mentor1 = User.objects.create_user(
            email="mr@bennet.org",
            first_name="Mr.",
            last_name="Bennet",
        )

        Profile.objects.create(
            user=mentor1,
            bio="Father, country gentleman",
            can_help =True,
            help_wanted=False
            )

        mentor2 = User.objects.create_user(
            email="charlotte@lucas.org",
            first_name="Charlotte",
            last_name="Lucas",
        )

        Profile.objects.create(
            user=mentor2,
            bio="Sensible, intelligent woman",
            can_help =True,
            help_wanted=False
            )

        not_a_mentor = User.objects.create_user(
            email="jenny@bennet.org",
            first_name="Jane Gardiner",
            last_name="Bennet",
        )

        Profile.objects.create(
            user=not_a_mentor,
            bio="Mother of five, host of nerves",
            can_help=False,
            help_wanted=False
        )

        another_mentee = User.objects.create_user(
            email="kitty@bennet.org",
            first_name="Kitty",
            last_name="Bennet",
        )

        Profile.objects.create(
            user=another_mentee,
            bio="Likes a man in uniform",
            can_help=False,
            help_wanted=True
        )

    def test_all_qualified(self):
        user = User.objects.get(email="elizabeth@bennet.org")
        mentor1 = User.objects.get(email="mr@bennet.org")
        mentor2 = User.objects.get(email="charlotte@lucas.org")
        mentor1_profile = Profile.objects.get(user__email="mr@bennet.org")
        mentor2_profile = Profile.objects.get(user__email="mr@bennet.org")
        c = Client()
        c.force_login(user)
        response = c.get('/search/')
        search_results = list(response.context_data['profile_list'])
        assert len(search_results) == 2
        assert mentor1_profile in search_results
        assert mentor2_profile in search_results

    def test_text_search(self):
        user = User.objects.get(email="elizabeth@bennet.org")
        mentor1 = User.objects.get(email="mr@bennet.org")
        mentor2 = User.objects.get(email="charlotte@lucas.org")
        c = Client()
        c.force_login(user)
        
        response = c.get('/search/?q=mr.+bennet')
        search_results = list(response.context_data['profile_list'])
        assert len(search_results) == 1
        assert search_results[0].user == mentor1

        response = c.get('/search/?q=sensible woman')
        search_results = list(response.context_data['profile_list'])
        assert len(search_results) == 1
        assert search_results[0].user == mentor2