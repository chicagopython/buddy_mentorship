import datetime as dt

from django.test import TransactionTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils import timezone

from .models import BuddyRequest
from apps.users.models import User


class BuddyRequestTest(TransactionTestCase):
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
