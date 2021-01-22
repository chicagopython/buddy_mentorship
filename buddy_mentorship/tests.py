import datetime as dt
import os

from django.test import (
    Client,
    override_settings,
    TestCase,
    override_settings,
    TransactionTestCase,
)
from django.core import mail
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from .models import BuddyRequest, BuddyRequestManager, Profile, Skill, Experience
from .views import (
    can_request_as_mentor,
    can_offer_to_mentor,
    send_request,
    existing_requests,
    required_experiences,
)

from apps.users.models import User


class CreateBuddyRequestTest(TransactionTestCase):
    @override_settings(EMAIL_HOST="localhost")
    def setUp(self):
        mentee = User.objects.create_user(email="mentee@user.com")
        Profile.objects.create(user=mentee)
        mentor = User.objects.create_user(email="mentor@user.com")
        Profile.objects.create(user=mentor)

    def test_create_buddy_request(self):
        mentee = User.objects.get(email="mentee@user.com")
        mentor = User.objects.get(email="mentor@user.com")
        msg = "test message"
        new_buddy_request = BuddyRequest.objects.create(
            requestor=mentee,
            requestee=mentor,
            message=msg,
            request_type=BuddyRequest.RequestType.REQUEST,
        )
        buddy_request = BuddyRequest.objects.get(requestor=mentee, requestee=mentor)
        assert new_buddy_request == buddy_request
        assert timezone.now() - buddy_request.request_sent > dt.timedelta(seconds=0)
        assert timezone.now() - buddy_request.request_sent < dt.timedelta(minutes=1)
        assert buddy_request.requestee == mentor
        assert buddy_request.requestor == mentee
        assert buddy_request.message == msg
        assert buddy_request.__str__() == (
            f"Request from mentee@user.com to mentor@user.com "
            f"on {buddy_request.request_sent.__str__()}"
        )

    def test_create_buddy_offer(self):
        mentee = User.objects.get(email="mentee@user.com")
        mentor = User.objects.get(email="mentor@user.com")
        msg = "test message"
        new_buddy_request = BuddyRequest.objects.create(
            requestee=mentee,
            requestor=mentor,
            message=msg,
            request_type=BuddyRequest.RequestType.OFFER,
        )
        buddy_request = BuddyRequest.objects.get(requestor=mentor, requestee=mentee)
        assert new_buddy_request == buddy_request
        assert timezone.now() - buddy_request.request_sent > dt.timedelta(seconds=0)
        assert timezone.now() - buddy_request.request_sent < dt.timedelta(minutes=1)
        assert buddy_request.requestee == mentee
        assert buddy_request.requestor == mentor
        assert buddy_request.message == msg
        assert buddy_request.__str__() == (
            f"Offer from mentor@user.com to mentee@user.com "
            f"on {buddy_request.request_sent.__str__()}"
        )


class ProfileTest(TransactionTestCase):
    def test_create_profile(self):
        new_user = User.objects.create_user(email="testprofile@user.com")
        user = User.objects.first()
        profile = Profile.objects.create(
            user=user,
            bio="i'm super interested in Python",
            looking_for_mentors=True,
            looking_for_mentees=False,
        )
        skill1, skill2 = (
            Skill.objects.create(skill="Django"),
            Skill.objects.create(skill="seaborn"),
        )

        Experience.objects.create(
            profile=profile, skill=skill1, level=4, exp_type=Experience.Type.CAN_HELP,
        )

        Experience.objects.create(
            profile=profile, skill=skill2, level=1, exp_type=Experience.Type.WANT_HELP,
        )

        with self.assertRaises(IntegrityError):
            Experience.objects.create(
                profile=profile,
                skill=skill2,
                level=1,
                exp_type=Experience.Type.WANT_HELP,
            )

        profileRecord = Profile.objects.get(user=user)
        self.assertEqual(profileRecord.bio, "i'm super interested in Python")

        experienceRecord1 = Experience.objects.get(profile=profile, skill=skill1)
        self.assertEqual(experienceRecord1.exp_type, Experience.Type.CAN_HELP)

        experienceRecord2 = Experience.objects.get(profile=profile, skill=skill2)
        self.assertEqual(experienceRecord2.exp_type, Experience.Type.WANT_HELP)

        skillRecord1 = Skill.objects.get(skill=skill1)
        self.assertEqual(skillRecord1.skill, "Django")

        skillRecord2 = Skill.objects.get(skill=skill2)
        self.assertEqual(skillRecord2.skill, "seaborn")

    def test_profile_without_own(self):
        user = User.objects.create_user(email="no_profile@user.com")
        profile_user = create_test_users(1, "profile_user", [])[0]
        profile = Profile.objects.get(user=profile_user)
        c = Client()
        c.force_login(user)
        response = c.get(f"/profile/{profile.id}",)
        assert response.status_code == 200

    def test_nonexistent_profile(self):
        user = User.objects.create_user(email="no_profile@user.com")
        if len(Profile.objects.all()) == 0:
            invalid_id = 1
        else:
            invalid_id = max([profile.id for profile in Profile.objects.all()]) + 100
        c = Client()
        c.force_login(user)
        response = c.get(f"/profile/{invalid_id}",)
        assert response.status_code == 404

    def test_profile_view(self):
        skill1 = Skill.objects.create(skill="python")
        skill2 = Skill.objects.create(skill="django")
        skill3 = Skill.objects.create(skill="numpy")
        skill4 = Skill.objects.create(skill="pandas")

        skill3.display_name = "Abracadabra"
        skill3.save()

        skills = [
            {"skill": skill1, "level": 4, "exp_type": Experience.Type.CAN_HELP},
            {"skill": skill2, "level": 3, "exp_type": Experience.Type.CAN_HELP},
            {"skill": skill3, "level": 2, "exp_type": Experience.Type.WANT_HELP},
            {"skill": skill4, "level": 1, "exp_type": Experience.Type.WANT_HELP},
        ]

        user = create_test_users(1, "user", skills)[0]
        profile = Profile.objects.get(user=user)

        exp1 = Experience.objects.get(profile=profile, skill=skill1)
        exp2 = Experience.objects.get(profile=profile, skill=skill2)
        exp3 = Experience.objects.get(profile=profile, skill=skill3)

        c = Client()
        c.force_login(user)
        response = c.get("/profile/",)
        assert response.status_code == 200
        assert response.context["can_request"] == False
        assert response.context["can_offer"] == False
        assert response.context["profile"] == Profile.objects.get(user=user)
        assert response.context["active_page"] == "profile"
        assert response.context["request_type"] == BuddyRequest.RequestType
        assert bytes("Abracadabra", "utf-8") in response.content
        assert bytes("numpy", "utf-8") not in response.content

    def test_short_bio(self):
        user = User.objects.create_user(email="user@user.com")

        # long first paragraph
        bio_parts = [
            "Lion turkish angora balinese russian blue devonshire rex ",
            "scottish fold ocelot. Panther. American bobtail egyptian mau. ",
            "Bobcat kitten ragdoll. American shorthair savannah or havana ",
            "brown american shorthair and kitten manx. Russian blue cougar, ",
            "yet cougar. Singapura tiger or tabby. Panther ocicat singapura. ",
            "Puma. Persian siberian. Jaguar sphynx. Cornish rex tabby ",
            "panther. Birman. Tiger. Bombay ragdoll cougar bengal. Norwegian ",
            "forest american bobtail but burmese but persian. Cornish rex. ",
            "Munchkin malkin and balinese yet munchkin thai cougar. Cougar ",
            "tabby russian blue singapura or malkin puma. Lion british ",
            "shorthair norwegian forest tomcat. Ocicat puma, yet thai.",
        ]
        bio = "".join(bio_parts)
        profile = Profile.objects.create(user=user, bio=bio)
        short_bio = "".join(
            bio_parts[:3] + ["brown american shorthair and kitten manx."]
        )
        assert profile.get_short_bio() == short_bio

        # multiple paragraphs
        profile.bio = """I am a person.

        My bio has two paragraphs."""
        assert profile.get_short_bio() == "I am a person."

        # short bio
        profile.bio = "I am a person."
        assert profile.get_short_bio() == "I am a person."

        # run-on sentence (don't do this)
        bio_parts = [
            "Lion turkish angora balinese russian blue devonshire rex ",
            "scottish fold ocelot Panther American bobtail egyptian mau ",
            "Bobcat kitten ragdoll American shorthair savannah or havana ",
            "brown american shorthair and kitten manx Russian blue cougar, ",
            "yet cougar. Singapura tiger or tabby Panther ocicat singapura ",
            "Puma Persian siberian Jaguar sphynx Cornish rex tabby ",
            "panther Birman Tiger Bombay ragdoll cougar bengal Norwegian ",
            "forest american bobtail but burmese but persian Cornish rex ",
            "Munchkin malkin and balinese yet munchkin thai cougar Cougar ",
            "tabby russian blue singapura or malkin puma Lion british ",
            "shorthair norwegian forest tomcat Ocicat puma, yet thai",
        ]
        profile.bio = "".join(bio_parts)
        assert profile.get_short_bio() == "".join(bio_parts[:4])

    def test_get_experiences(self):
        skills = [
            Skill.objects.create(skill=name)
            for name in [
                "pandas",
                "flask",
                "numpy",
                "python",
                "django",
                "pytorch",
                "react",
                "pytest",
            ]
        ]

        user = create_test_users(
            1,
            "user",
            [
                {
                    "skill": skills[i],
                    "level": i + 1,
                    "exp_type": Experience.Type.WANT_HELP,
                }
                for i in range(0, 4)
            ]
            + [
                {
                    "skill": skills[i],
                    "level": 9 - i,
                    "exp_type": Experience.Type.CAN_HELP,
                }
                for i in range(4, 8)
            ],
        )[0]

        profile = Profile.objects.get(user=user)

        exps = [
            Experience.objects.get(profile=profile, skill=skill) for skill in skills
        ]

        assert list(profile.get_help_wanted()) == exps[:4]

        assert list(profile.get_can_help()) == exps[4:8]

        assert list(profile.get_top_want_help()) == exps[:3]

        assert list(profile.get_top_can_help()) == exps[4:7]

    def test_get_experiences_with_query(self):
        pandas, flask = (
            Skill.objects.create(skill=name) for name in ["pandas", "flask",]
        )

        user = create_test_users(
            1,
            "user",
            [
                {"skill": pandas, "level": 3, "exp_type": Experience.Type.CAN_HELP,},
                {"skill": flask, "level": 3, "exp_type": Experience.Type.CAN_HELP,},
            ],
        )[0]

        profile = Profile.objects.get(user=user)

        pandas_exp = Experience.objects.get(profile=profile, skill=pandas)
        flask_exp = Experience.objects.get(profile=profile, skill=flask)

        assert list(profile.get_can_help("pandas")) == [pandas_exp, flask_exp]

        assert list(profile.get_can_help("flask")) == [flask_exp, pandas_exp]

        assert list(profile.get_top_can_help("pandas")) == [pandas_exp, flask_exp]

        assert list(profile.get_top_can_help("flask")) == [flask_exp, pandas_exp]

        assert list(profile.get_top_can_help("user flask")) == [flask_exp, pandas_exp]

    def test_why_no_request(self):
        pandas = Skill.objects.create(skill="pandas")

        user = create_test_users(
            1,
            "user",
            [{"skill": pandas, "level": 1, "exp_type": Experience.Type.WANT_HELP,},],
        )[0]

        profile_user = create_test_users(
            1, "profile_user", [], looking_for_mentees=True,
        )[0]

        profile = Profile.objects.get(user=profile_user)

        c = Client()
        c.force_login(user)

        response = c.get(f"/profile/{profile.id}",)
        assert not response.context["can_request"]
        assert not response.context["cannot_request_not_looking"]
        assert response.context["cannot_request_no_skills"]

        Experience.objects.create(
            profile=profile, skill=pandas, level=4, exp_type=Experience.Type.CAN_HELP
        )

        response = c.get(f"/profile/{profile.id}",)
        assert response.context["can_request"]
        assert not response.context["cannot_request_not_looking"]
        assert not response.context["cannot_request_no_skills"]

        profile.looking_for_mentees = False
        profile.save()

        response = c.get(f"/profile/{profile.id}",)
        assert not response.context["can_request"]
        assert response.context["cannot_request_not_looking"]
        assert not response.context["cannot_request_no_skills"]

    def test_why_no_offer(self):
        pandas = Skill.objects.create(skill="pandas")

        user = create_test_users(
            1,
            "user",
            [{"skill": pandas, "level": 4, "exp_type": Experience.Type.CAN_HELP,},],
        )[0]

        profile_user = create_test_users(
            1, "profile_user", [], looking_for_mentors=True,
        )[0]

        profile = Profile.objects.get(user=profile_user)

        c = Client()
        c.force_login(user)

        response = c.get(f"/profile/{profile.id}",)
        assert not response.context["can_offer"]
        assert not response.context["cannot_offer_not_looking"]
        assert response.context["cannot_offer_no_skills"]

        Experience.objects.create(
            profile=profile, skill=pandas, level=1, exp_type=Experience.Type.WANT_HELP
        )

        response = c.get(f"/profile/{profile.id}",)
        assert response.context["can_offer"]
        assert not response.context["cannot_offer_not_looking"]
        assert not response.context["cannot_offer_no_skills"]

        profile.looking_for_mentors = False
        profile.save()

        response = c.get(f"/profile/{profile.id}",)
        assert not response.context["can_offer"]
        assert response.context["cannot_offer_not_looking"]
        assert not response.context["cannot_offer_no_skills"]


class SendBuddyRequestTest(TestCase):
    def setUp(self):

        skill1, skill2 = (
            Skill.objects.create(skill="pandas"),
            Skill.objects.create(skill="Flask"),
        )

        create_test_users(
            1,
            "mentor",
            [{"skill": skill1, "level": 2, "exp_type": Experience.Type.CAN_HELP}],
            looking_for_mentees=True,
            looking_for_mentors=False,
        )

        create_test_users(
            1,
            "mentee",
            [{"skill": skill1, "level": 3, "exp_type": Experience.Type.WANT_HELP}],
            looking_for_mentors=True,
            looking_for_mentees=False,
        )

        create_test_users(
            1, "someone", [], looking_for_mentors=False, looking_for_mentees=False,
        )

    def test_existing_requests(self):
        mentee = User.objects.get(email="mentee0@buddy.com")
        mentor = User.objects.get(email="mentor0@buddy.com")

        assert not existing_requests(mentee, mentor)

        buddy_request = BuddyRequest.objects.create(
            requestor=mentee,
            requestee=mentor,
            message="Please help me!",
            request_type=BuddyRequest.RequestType.REQUEST,
        )

        assert existing_requests(mentee, mentor)

        buddy_request.delete()
        assert not existing_requests(mentee, mentor)
        buddy_offer = BuddyRequest.objects.create(
            requestor=mentor,
            requestee=mentee,
            message="I can help you!",
            request_type=BuddyRequest.RequestType.OFFER,
        )

        assert existing_requests(mentee, mentor)

    def test_required_experiences(self):
        mentee = User.objects.get(email="mentee0@buddy.com")
        mentor = User.objects.get(email="mentor0@buddy.com")
        someone = User.objects.get(email="someone0@buddy.com")
        assert required_experiences(mentee, mentor)
        assert not required_experiences(mentor, mentee)
        assert not required_experiences(mentee, someone)
        assert not required_experiences(someone, mentee)
        assert not required_experiences(someone, mentor)
        assert not required_experiences(mentor, someone)

    def test_can_request_as_mentor(self):
        mentee = User.objects.get(email="mentee0@buddy.com")
        mentee_profile = Profile.objects.get(user=mentee)
        mentor = User.objects.get(email="mentor0@buddy.com")
        mentor_profile = Profile.objects.get(user=mentor)
        someone = User.objects.get(email="someone0@buddy.com")
        assert can_request_as_mentor(mentee, mentor)

        mentor.is_active = False
        assert not can_request_as_mentor(mentee, mentor)
        mentor.is_active = True

        mentor_profile.looking_for_mentees = False
        mentor_profile.save()
        assert not can_request_as_mentor(mentee, mentor)

        mentor_profile.looking_for_mentees = True

        buddy_request = BuddyRequest.objects.create(
            requestor=mentee,
            requestee=mentor,
            message="Please help me!",
            request_type=BuddyRequest.RequestType.REQUEST,
        )
        assert not can_request_as_mentor(mentee, someone)
        assert not can_request_as_mentor(someone, mentor)
        assert not can_request_as_mentor(mentee, mentor)
        buddy_request.delete()

    def test_can_offer_to_mentor(self):
        mentee = User.objects.get(email="mentee0@buddy.com")
        mentee_profile = Profile.objects.get(user=mentee)
        mentor = User.objects.get(email="mentor0@buddy.com")
        mentor_profile = Profile.objects.get(user=mentor)
        someone = User.objects.get(email="someone0@buddy.com")
        assert can_offer_to_mentor(mentor, mentee)

        mentee.is_active = False
        assert not can_offer_to_mentor(mentor, mentee)
        mentee.is_active = True

        mentee_profile.looking_for_mentors = False
        mentee_profile.save()
        assert not can_offer_to_mentor(mentor, mentee)

        mentee_profile.looking_for_mentors = True

        buddy_request = BuddyRequest.objects.create(
            requestor=mentor,
            requestee=mentee,
            message="I can help you!",
            request_type=BuddyRequest.RequestType.OFFER,
        )
        assert not can_offer_to_mentor(mentor, someone)
        assert not can_offer_to_mentor(someone, mentor)
        assert not can_offer_to_mentor(mentor, mentee)
        buddy_request.delete()

    def test_send_request(self):
        c = Client()
        mentee = User.objects.get(email="mentee0@buddy.com")
        mentor = User.objects.get(email="mentor0@buddy.com")
        mentee_profile = Profile.objects.get(user=mentee)
        assert not BuddyRequest.objects.filter(
            requestor=mentee,
            requestee=mentor,
            request_type=BuddyRequest.RequestType.REQUEST,
        )

        c.force_login(mentee)
        response = c.post(
            f"/send_request/{mentor.uuid}",
            {
                "message": "Please be my mentor.",
                "request_type": BuddyRequest.RequestType.REQUEST,
            },
        )
        assert response.status_code == 302
        assert BuddyRequest.objects.get(requestor=mentee)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "New ChiPy Mentorship Request!"
        profile_link = f"<a href='{os.getenv('APP_URL')}{reverse('profile',args=[mentee_profile.id])}'>"
        mentee_name = f"{mentee.first_name} {mentee.last_name}"
        sent_message = mail.outbox[0].alternatives[0][0]
        assert profile_link in sent_message
        assert mentee_name in sent_message
        assert mentor.email in mail.outbox[0].recipients()

        response = c.post(
            f"/send_request/{mentor.uuid}",
            {
                "message": "Please be my mentor.",
                "request_type": BuddyRequest.RequestType.REQUEST,
            },
        )
        assert response.status_code == 403
        assert len(BuddyRequest.objects.filter(requestor=mentee, requestee=mentor)) == 1

    def test_accept_request(self):
        c = Client()
        mentee = User.objects.get(email="mentee0@buddy.com")
        mentor = User.objects.get(email="mentor0@buddy.com")
        mentor_profile = Profile.objects.get(user=mentor)
        buddy_request = BuddyRequest.objects.create(
            requestor=mentee,
            requestee=mentor,
            message="Please be my mentor",
            request_type=BuddyRequest.RequestType.REQUEST,
        )
        buddy_request.status = 1
        buddy_request.save()

        assert len(mail.outbox) == 2
        assert mail.outbox[1].subject == "ChiPy Mentorship Request Accepted!"
        profile_link = f"<a href='{os.getenv('APP_URL')}{reverse('profile',args=[mentor_profile.id])}'>"
        mentor_name = f"{mentor.first_name} {mentor.last_name}"
        sent_message = mail.outbox[1].alternatives[0][0]
        assert profile_link in sent_message
        assert mentor_name in sent_message
        assert mentee.email in mail.outbox[1].recipients()

    def test_reject_request(self):
        c = Client()
        mentee = User.objects.get(email="mentee0@buddy.com")
        mentor = User.objects.get(email="mentor0@buddy.com")
        buddy_request = BuddyRequest.objects.create(
            requestor=mentee,
            requestee=mentor,
            request_type=BuddyRequest.RequestType.REQUEST,
        )
        buddy_request.status = BuddyRequest.Status.REJECTED
        buddy_request.save()

        assert len(mail.outbox) == 1

    def test_complete_request(self):
        c = Client()
        mentee = User.objects.get(email="mentee0@buddy.com")
        mentor = User.objects.get(email="mentor0@buddy.com")
        mentor_profile = Profile.objects.get(user=mentor)
        mentee_profile = Profile.objects.get(user=mentee)
        buddy_request = BuddyRequest.objects.create(
            requestor=mentee,
            requestee=mentor,
            request_type=BuddyRequest.RequestType.REQUEST,
            status=BuddyRequest.Status.ACCEPTED,
        )

        assert len(mail.outbox) == 1

        buddy_request.status = BuddyRequest.Status.COMPLETED
        buddy_request.save()

        assert len(mail.outbox) == 3

        email_to_mentor = mail.outbox[1]
        assert email_to_mentor.subject == "ChiPy Mentorship Completed"
        mentee_profile_link = f"<a href='{os.getenv('APP_URL')}{reverse('profile',args=[mentee_profile.id])}'>"
        mentee_name = f"{mentee.first_name} {mentee.last_name}"
        message_to_mentor = email_to_mentor.alternatives[0][0]
        assert mentee_profile_link in message_to_mentor
        assert mentee_name in message_to_mentor
        assert mentor.email in email_to_mentor.recipients()

        email_to_mentee = mail.outbox[2]
        assert email_to_mentee.subject == "ChiPy Mentorship Completed"
        mentor_profile_link = f"<a href='{os.getenv('APP_URL')}{reverse('profile',args=[mentor_profile.id])}'>"
        mentor_name = f"{mentor.first_name} {mentor.last_name}"
        message_to_mentee = email_to_mentee.alternatives[0][0]
        assert mentor_profile_link in message_to_mentee
        assert mentor_name in message_to_mentee
        assert mentee.email in email_to_mentee.recipients()


class SendBuddyOfferTest(TestCase):
    def setUp(self):
        skill1, skill2 = (
            Skill.objects.create(skill="pandas"),
            Skill.objects.create(skill="Flask"),
        )

        create_test_users(
            1,
            "mentor",
            [{"skill": skill1, "level": 2, "exp_type": Experience.Type.CAN_HELP}],
        )

        create_test_users(
            1,
            "mentee",
            [{"skill": skill1, "level": 3, "exp_type": Experience.Type.WANT_HELP}],
        )

        create_test_users(
            1, "someone", [],
        )

    def test_send_offer(self):
        c = Client()
        mentee = User.objects.get(email="mentee0@buddy.com")
        mentor = User.objects.get(email="mentor0@buddy.com")
        mentor_profile = Profile.objects.get(user=mentor)
        assert not BuddyRequest.objects.filter(
            requestor=mentor,
            requestee=mentee,
            request_type=BuddyRequest.RequestType.OFFER,
        )

        c.force_login(mentor)
        response = c.post(
            f"/send_request/{mentee.uuid}",
            {
                "message": "Please be my mentee.",
                "request_type": BuddyRequest.RequestType.OFFER,
            },
        )
        assert response.status_code == 302
        assert BuddyRequest.objects.get(requestor=mentor)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "New ChiPy Mentorship Offer!"
        profile_link = f"<a href='{os.getenv('APP_URL')}{reverse('profile',args=[mentor_profile.id])}'>"
        mentor_name = f"{mentor.first_name} {mentor.last_name}"
        sent_message = mail.outbox[0].alternatives[0][0]
        assert profile_link in sent_message
        assert mentor_name in sent_message
        assert mentee.email in mail.outbox[0].recipients()

        response = c.post(
            f"/send_request/{mentee.uuid}",
            {
                "message": "Please be my mentee.",
                "request_type": BuddyRequest.RequestType.OFFER,
            },
        )
        assert response.status_code == 403
        assert len(BuddyRequest.objects.filter(requestor=mentor, requestee=mentee)) == 1

    def test_accept_offer(self):
        c = Client()
        mentee = User.objects.get(email="mentee0@buddy.com")
        mentor = User.objects.get(email="mentor0@buddy.com")
        mentee_profile = Profile.objects.get(user=mentee)
        buddy_request = BuddyRequest.objects.create(
            requestor=mentor,
            requestee=mentee,
            message="Please be my mentee",
            request_type=BuddyRequest.RequestType.OFFER,
        )
        buddy_request.status = 1
        buddy_request.save()

        assert len(mail.outbox) == 2
        assert mail.outbox[1].subject == "ChiPy Mentorship Offer Accepted!"
        profile_link = f"<a href='{os.getenv('APP_URL')}{reverse('profile',args=[mentee_profile.id])}'>"
        mentee_name = f"{mentee.first_name} {mentee.last_name}"
        sent_message = mail.outbox[1].alternatives[0][0]
        assert profile_link in sent_message
        assert mentee_name in sent_message
        assert mentor.email in mail.outbox[1].recipients()

    def test_reject_offer(self):
        c = Client()
        mentee = User.objects.get(email="mentee0@buddy.com")
        mentor = User.objects.get(email="mentor0@buddy.com")
        buddy_request = BuddyRequest.objects.create(
            requestor=mentor,
            requestee=mentee,
            request_type=BuddyRequest.RequestType.OFFER,
        )
        buddy_request.status = 2
        buddy_request.save()

        # right now this doesn't do anything
        assert len(mail.outbox) == 1

    def test_complete_offer(self):
        c = Client()
        mentee = User.objects.get(email="mentee0@buddy.com")
        mentor = User.objects.get(email="mentor0@buddy.com")
        mentor_profile = Profile.objects.get(user=mentor)
        mentee_profile = Profile.objects.get(user=mentee)
        buddy_request = BuddyRequest.objects.create(
            requestor=mentor,
            requestee=mentee,
            request_type=BuddyRequest.RequestType.OFFER,
            status=BuddyRequest.Status.ACCEPTED,
        )

        assert len(mail.outbox) == 1

        buddy_request.status = BuddyRequest.Status.COMPLETED
        buddy_request.save()

        assert len(mail.outbox) == 3

        email_to_mentee = mail.outbox[1]
        assert email_to_mentee.subject == "ChiPy Mentorship Completed"
        mentor_profile_link = f"<a href='{os.getenv('APP_URL')}{reverse('profile',args=[mentor_profile.id])}'>"
        mentor_name = f"{mentor.first_name} {mentor.last_name}"
        message_to_mentee = email_to_mentee.alternatives[0][0]
        assert mentor_profile_link in message_to_mentee
        assert mentor_name in message_to_mentee
        assert mentee.email in email_to_mentee.recipients()

        email_to_mentor = mail.outbox[2]
        assert email_to_mentor.subject == "ChiPy Mentorship Completed"
        mentee_profile_link = f"<a href='{os.getenv('APP_URL')}{reverse('profile',args=[mentee_profile.id])}'>"
        mentee_name = f"{mentee.first_name} {mentee.last_name}"
        message_to_mentor = email_to_mentor.alternatives[0][0]
        assert mentee_profile_link in message_to_mentor
        assert mentee_name in message_to_mentor
        assert mentor.email in email_to_mentor.recipients()


class BuddyRequestModelTest(TestCase):
    def setUp(self):
        hari = User.objects.create_user(
            email="me@hariseldon", first_name="Hari", last_name="Seldon",
        )
        elizabeth = User.objects.create_user(
            email="elizabeth@bennet.org", first_name="Elizabeth", last_name="Bennet",
        )
        Profile.objects.create(user=hari)
        Profile.objects.create(user=elizabeth)

    def test_no_requests(self):
        hari = User.objects.get(email="me@hariseldon")
        elizabeth = User.objects.get(email="elizabeth@bennet.org")
        assert (
            BuddyRequest.objects.find_by_users(
                hari, elizabeth, BuddyRequest.RequestType.REQUEST
            )
            is None
        )
        assert (
            BuddyRequest.objects.find_by_users(
                elizabeth, hari, BuddyRequest.RequestType.REQUEST
            )
            is None
        )
        assert (
            BuddyRequest.objects.find_by_users(
                hari, elizabeth, BuddyRequest.RequestType.OFFER
            )
            is None
        )
        assert (
            BuddyRequest.objects.find_by_users(
                elizabeth, hari, BuddyRequest.RequestType.OFFER
            )
            is None
        )

    def test_mentor_request(self):
        hari = User.objects.get(email="me@hariseldon")
        elizabeth = User.objects.get(email="elizabeth@bennet.org")
        request = BuddyRequest.objects.create(
            requestor=hari,
            requestee=elizabeth,
            message="",
            request_type=BuddyRequest.RequestType.REQUEST,
            status=BuddyRequest.Status.NEW,
        )
        assert (
            BuddyRequest.objects.find_by_users(
                hari, elizabeth, BuddyRequest.RequestType.REQUEST
            )
            == request
        )
        assert (
            BuddyRequest.objects.find_by_users(
                elizabeth, hari, BuddyRequest.RequestType.REQUEST
            )
            is None
        )
        assert (
            BuddyRequest.objects.find_by_users(
                hari, elizabeth, BuddyRequest.RequestType.OFFER
            )
            is None
        )
        assert (
            BuddyRequest.objects.find_by_users(
                elizabeth, hari, BuddyRequest.RequestType.OFFER
            )
            is None
        )

    def test_mentor_offer(self):
        hari = User.objects.get(email="me@hariseldon")
        elizabeth = User.objects.get(email="elizabeth@bennet.org")
        request = BuddyRequest.objects.create(
            requestor=hari,
            requestee=elizabeth,
            message="",
            request_type=BuddyRequest.RequestType.OFFER,
            status=BuddyRequest.Status.NEW,
        )
        assert (
            BuddyRequest.objects.find_by_users(
                hari, elizabeth, BuddyRequest.RequestType.REQUEST
            )
            is None
        )
        assert (
            BuddyRequest.objects.find_by_users(
                elizabeth, hari, BuddyRequest.RequestType.REQUEST
            )
            is None
        )
        assert (
            BuddyRequest.objects.find_by_users(
                hari, elizabeth, BuddyRequest.RequestType.OFFER
            )
            == request
        )
        assert (
            BuddyRequest.objects.find_by_users(
                elizabeth, hari, BuddyRequest.RequestType.OFFER
            )
            is None
        )


class ProfileEditTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            email="me@hariseldon", first_name="Hari", last_name="Seldon",
        )

    def test_edit_myself(self):
        user = User.objects.get(email="me@hariseldon")
        c = Client()
        c.force_login(user)

        response = c.post(
            f"/profile_edit/",
            {
                "first_name": "new name",
                "last_name": "new last name",
                "email": "newemail@example.com",
                "bio": "predicting the future",
                "looking_for_mentors": True,
                "looking_for_mentees": False,
            },
        )
        user.refresh_from_db()
        assert user.first_name == "new name"
        assert user.last_name == "new last name"
        assert user.email == "newemail@example.com"
        profile = Profile.objects.get(user=user)
        assert profile.bio == "predicting the future"
        assert profile.looking_for_mentors
        assert not profile.looking_for_mentees

    def test_edit_my_profile(self):
        user = User.objects.get(email="me@hariseldon")
        profile = Profile.objects.create(user=user, bio="no future")
        c = Client()
        c.force_login(user)

        response = c.post(
            f"/profile_edit/",
            {
                "first_name": "new name",
                "last_name": "new last name",
                "email": "newemail@example.com",
                "bio": "predicting the future",
                "looking_for_mentors": False,
                "looking_for_mentees": True,
            },
        )
        profile = Profile.objects.get(user=user)
        assert profile.bio == "predicting the future"
        assert not profile.looking_for_mentors
        assert profile.looking_for_mentees

    def test_edit_profile_no_bio(self):
        user = User.objects.get(email="me@hariseldon")
        profile = Profile.objects.create(user=user)
        c = Client()
        c.force_login(user)

        response = c.post(
            f"/profile_edit/",
            {
                "first_name": "new name",
                "last_name": "new last name",
                "email": "newemail@example.com",
                "bio": "",
            },
        )
        profile = Profile.objects.get(user=user)
        assert profile.bio == ""

    def test_edit_profile_no_last_name(self):
        user = User.objects.create_user(email="hari@hariseldon", first_name="Hari")
        user.last_name = "Seldon"
        user.save()

        profile = Profile.objects.create(user=user)
        c = Client()
        c.force_login(user)

        response = c.post(
            f"/profile_edit/",
            {
                "first_name": "new name",
                "last_name": "",
                "email": "newemail@example.com",
                "bio": "this is a bio",
            },
        )
        user.refresh_from_db()
        assert user.last_name == ""


class SearchTest(TestCase):
    def setUp(self):

        skill1, skill2 = (
            Skill.objects.create(skill="pandas"),
            Skill.objects.create(skill="Flask"),
        )

        skill2.display_name = "Something Else"
        skill2.save()

        user = User.objects.create_user(
            email="elizabeth@bennet.org", first_name="Elizabeth", last_name="Bennet",
        )

        profile_user = Profile.objects.create(
            user=user, bio="", looking_for_mentors=False, looking_for_mentees=False
        )

        Experience.objects.create(
            profile=profile_user,
            skill=skill2,
            level=5,
            exp_type=Experience.Type.WANT_HELP,
        )

        mentor1 = User.objects.create_user(
            email="mr@bennet.org", first_name="Mr.", last_name="Bennet",
        )

        profile_mentor1 = Profile.objects.create(
            user=mentor1,
            bio="Father, country gentleman. Friend of the Lucas family.",
            looking_for_mentors=False,
            looking_for_mentees=True,
        )

        Experience.objects.create(
            profile=profile_mentor1,
            skill=skill1,
            level=1,
            exp_type=Experience.Type.CAN_HELP,
        )

        Experience.objects.create(
            profile=profile_mentor1,
            skill=skill2,
            level=3,
            exp_type=Experience.Type.CAN_HELP,
        )

        mentor2 = User.objects.create_user(
            email="charlotte@lucas.org", first_name="Charlotte", last_name="Lucas",
        )

        profile_mentor2 = Profile.objects.create(
            user=mentor2,
            bio="Sensible, intelligent woman. Daughter of Sir William Lucas.",
            looking_for_mentors=False,
            looking_for_mentees=True,
        )

        Experience.objects.create(
            profile=profile_mentor2,
            skill=skill2,
            level=3,
            exp_type=Experience.Type.CAN_HELP,
        )

        inactive_mentor = User.objects.create_user(
            email="mary@crawford.com", first_name="Mary", last_name="Crawford",
        )

        profile_inactive_mentor = Profile.objects.create(
            user=inactive_mentor,
            bio="I mentor, but am too busy right now.",
            looking_for_mentees=False,
            looking_for_mentors=False,
        )

        Experience.objects.create(
            profile=profile_inactive_mentor,
            skill=skill2,
            level=3,
            exp_type=Experience.Type.CAN_HELP,
        )

        not_a_mentor = User.objects.create_user(
            email="jenny@bennet.org", first_name="Jane Gardiner", last_name="Bennet",
        )

        profile_not_a_mentor = Profile.objects.create(
            user=not_a_mentor, bio="Mother of five, host of nerves"
        )

        create_test_users(
            1,
            "mentee0",
            [
                {"skill": skill1, "level": 2, "exp_type": Experience.Type.WANT_HELP},
                {"skill": skill2, "level": 1, "exp_type": Experience.Type.WANT_HELP},
            ],
            looking_for_mentees=False,
            looking_for_mentors=True,
        )

        create_test_users(
            1,
            "mentee1",
            [{"skill": skill1, "level": 1, "exp_type": Experience.Type.WANT_HELP},],
            looking_for_mentees=False,
            looking_for_mentors=True,
        )

        create_test_users(
            1,
            "inactive_mentee",
            [{"skill": skill1, "level": 1, "exp_type": Experience.Type.WANT_HELP},],
            looking_for_mentees=False,
            looking_for_mentors=False,
        )

    def test_all_mentors(self):
        user = User.objects.get(email="elizabeth@bennet.org")
        mentor1 = User.objects.get(email="mr@bennet.org")
        mentor2 = User.objects.get(email="charlotte@lucas.org")
        mentor1_profile = Profile.objects.get(user__email="mr@bennet.org")
        mentor2_profile = Profile.objects.get(user__email="mr@bennet.org")
        c = Client()
        c.force_login(user)
        response = c.get("/search/")
        search_results = list(response.context_data["profile_list"])
        assert len(search_results) == 2
        assert mentor1_profile in search_results
        assert mentor2_profile in search_results
        assert bytes("Something Else", "utf-8") in response.content
        assert bytes("Flask", "utf-8") not in response.content

    def test_mentor_text_search(self):
        user = User.objects.get(email="elizabeth@bennet.org")
        mentor1 = User.objects.get(email="mr@bennet.org")
        mentor2 = User.objects.get(email="charlotte@lucas.org")
        c = Client()
        c.force_login(user)

        response = c.get("/search/?q=mr.+bennet")
        search_results = list(response.context_data["profile_list"])
        assert len(search_results) == 1
        assert search_results[0].user == mentor1

        response = c.get("/search/?q=sensible woman")
        search_results = list(response.context_data["profile_list"])
        assert len(search_results) == 1
        assert search_results[0].user == mentor2

        response = c.get("/search/?q=flask")
        search_results = list(response.context_data["profile_list"])
        assert len(search_results) == 2
        search_result_users = [result.user for result in search_results]
        assert mentor1 in search_result_users
        assert mentor2 in search_result_users

    def test_mentor_text_search_order(self):
        user = User.objects.get(email="elizabeth@bennet.org")
        mentor1 = User.objects.get(email="mr@bennet.org")
        mentor2 = User.objects.get(email="charlotte@lucas.org")
        c = Client()
        c.force_login(user)

        response = c.get("/search/?q=lucas")
        search_results = list(response.context_data["profile_list"])
        assert len(search_results) == 2
        search_result_users = [result.user for result in search_results]
        assert search_result_users[0] == mentor2
        assert search_result_users[1] == mentor1

    def test_all_mentees(self):
        user = User.objects.get(email="elizabeth@bennet.org")
        mentee00 = User.objects.get(email="mentee00@buddy.com")
        mentee10 = User.objects.get(email="mentee10@buddy.com")
        c = Client()
        c.force_login(user)
        response = c.get("/search/?type=mentee")
        search_results = list(response.context_data["profile_list"])
        search_result_users = [result.user for result in search_results]
        assert len(search_results) == 2
        assert mentee00 in search_result_users
        assert mentee10 in search_result_users

    def test_mentor_search_skill_order(self):
        user = User.objects.get(email="elizabeth@bennet.org")
        mentor1 = User.objects.get(email="mr@bennet.org")
        mentor2 = User.objects.get(email="charlotte@lucas.org")
        flask_exp = Experience.objects.get(profile__user=mentor1, skill__skill="Flask")
        pandas_exp = Experience.objects.get(
            profile__user=mentor1, skill__skill="pandas"
        )
        c = Client()
        c.force_login(user)
        response = c.get("/search/?q=gentleman+pandas&type=mentor")
        search_results = list(response.context_data["results"])
        assert len(search_results) == 1
        result = search_results[0]
        assert result["profile"].user == mentor1
        assert list(result["can_help"]) == [pandas_exp, flask_exp]

        response = c.get("/search/?type=mentor&q=gentleman+flask")
        search_results = list(response.context_data["results"])
        assert len(search_results) == 2
        assert search_results[0]["profile"].user == mentor1
        assert list(search_results[0]["can_help"]) == [flask_exp, pandas_exp]
        assert search_results[1]["profile"].user == mentor2
        assert list(search_results[1]["can_help"]) == [
            Experience.objects.get(profile__user=mentor2, skill__skill="Flask")
        ]

    def test_user_status(self):
        user = User.objects.get(email="elizabeth@bennet.org")
        c = Client()
        c.force_login(user)

        response = c.get("/search/")
        assert response.context_data["looking_for_mentors"] == False
        assert response.context_data["looking_for_mentees"] == False

        profile = Profile.objects.get(user=user)

        response = c.get("/search/")
        assert response.context_data["looking_for_mentors"] == False
        assert response.context_data["looking_for_mentees"] == False

        profile.looking_for_mentors = True
        profile.save()
        response = c.get("/search/?type=mentee")
        assert response.context_data["looking_for_mentors"] == True
        assert response.context_data["looking_for_mentees"] == False

        profile.looking_for_mentees = True
        profile.save()
        response = c.get("/search/?q=hi")
        assert response.context_data["looking_for_mentors"] == True
        assert response.context_data["looking_for_mentees"] == True

    def test_page_navigation(self):
        user = User.objects.get(email="elizabeth@bennet.org")
        weird_char_skill = Skill.objects.create(skill="data+")
        create_test_users(
            15,
            "page_tester",
            [
                {
                    "skill": weird_char_skill,
                    "level": 5,
                    "exp_type": Experience.Type.CAN_HELP,
                }
            ],
        )
        c = Client()
        c.force_login(user)
        response = c.get("/search/?q=data%2B&type=mentor&page=2")
        assert response.status_code == 200

        first_page_url = response.context_data["first_page_url"]
        assert first_page_url == "?q=data%2B&type=mentor&page=1"
        prev_page_url = response.context_data["prev_page_url"]
        assert prev_page_url == "?q=data%2B&type=mentor&page=1"
        next_page_url = response.context_data["next_page_url"]
        assert next_page_url == "?q=data%2B&type=mentor&page=3"
        last_page_url = response.context_data["last_page_url"]
        assert last_page_url == "?q=data%2B&type=mentor&page=last"

        response = c.get(f"/search/{prev_page_url}")
        assert response.status_code == 200
        response = c.get(f"/search/{next_page_url}")
        assert response.status_code == 200
        response = c.get(f"/search/{last_page_url}")
        assert response.status_code == 200


class SkillTest(TestCase):
    def setUp(self):
        create_test_users(1, "user", [])

    def test_skill_search(self):
        Skill.objects.create(skill="python", display_name="Python")
        Skill.objects.create(skill="django", display_name="Django")
        c = Client()
        user = User.objects.get(email="user0@buddy.com")
        c.force_login(user)

        response = c.get("/skill?term=o")
        assert response.json() == ["Python", "Django"]

        response = c.get("/skill?term=thon")
        assert response.json() == ["Python"]

        response = c.get("/skill?term=PyT")
        assert response.json() == ["Python"]

    def test_create_skill(self):
        assert not Skill.objects.filter(skill="python")
        Skill.objects.create(skill="python")
        python = Skill.objects.get(skill="python")
        assert python
        assert python.display_name == "Python"
        with self.assertRaises(IntegrityError):
            Skill.objects.create(skill="python")

    def test_update_experience_view(self):
        user = User.objects.get(email="user0@buddy.com")
        profile = Profile.objects.get(user=user)
        skill = Skill.objects.create(skill="pandas")
        exp = Experience.objects.create(
            profile=profile, skill=skill, exp_type=Experience.Type.WANT_HELP, level=1
        )
        c = Client()
        c.force_login(user)

        response = c.post(f"/edit_skill/{exp.id}", {"exp_type": 1, "level": 3},)
        exp = Experience.objects.get(profile=profile, skill=skill)
        assert exp.exp_type == Experience.Type.CAN_HELP and exp.level == 3

    def test_delete_experience_view(self):
        user = User.objects.get(email="user0@buddy.com")
        profile = Profile.objects.get(user=user)
        skill = Skill.objects.create(skill="pandas")
        exp = Experience.objects.create(
            profile=profile, skill=skill, exp_type=Experience.Type.CAN_HELP, level=1
        )
        c = Client()
        c.force_login(user)

        response = c.post(f"/delete_skill/{exp.id}", follow=True)
        assert not Experience.objects.filter(profile=profile, skill=skill)

    def test_add_skill_view(self):
        user = User.objects.get(email="user0@buddy.com")
        profile = Profile.objects.get(user=user)
        c = Client()
        c.force_login(user)

        # skill didn't exist
        response = c.post(
            f"/add_skill/0", {"exp_type": 0, "skill": "django", "level": 3,},
        )
        new_skill = Skill.objects.get(skill="django")
        exp = Experience.objects.get(skill=new_skill, profile=profile)
        assert exp.exp_type == Experience.Type.WANT_HELP and exp.level == 3

        # experience existed
        response = c.post(
            f"/add_skill/1", {"exp_type": 1, "skill": "django", "level": 4,},
        )
        exp = Experience.objects.get(skill=new_skill, profile=profile)
        response = c.get(f"/edit_skill/{exp.id}")

        # skill existed
        new_skill_2 = Skill.objects.create(skill="numpy")
        response = c.post(
            f"/add_skill/1", {"exp_type": 1, "skill": "numpy", "level": 4,},
        )
        exp = Experience.objects.get(skill=new_skill_2, profile=profile)
        assert exp.exp_type == Experience.Type.CAN_HELP and exp.level == 4


class CompleteMentorshipViewTest(TestCase):
    def setUp(self):
        skill1 = Skill.objects.create(skill="pandas")

        mentor = create_test_users(
            1,
            "mentor",
            [{"skill": skill1, "level": 2, "exp_type": Experience.Type.CAN_HELP}],
            looking_for_mentees=True,
            looking_for_mentors=False,
        )[0]

        mentee = create_test_users(
            1,
            "mentee",
            [{"skill": skill1, "level": 3, "exp_type": Experience.Type.WANT_HELP}],
            looking_for_mentors=True,
            looking_for_mentees=False,
        )[0]

        create_test_users(
            1, "someone", [],
        )

        BuddyRequest.objects.create(
            requestor=mentee,
            requestee=mentor,
            message="",
            request_type=BuddyRequest.RequestType.REQUEST,
            status=BuddyRequest.Status.ACCEPTED
        )

    def test_requestor_complete_mentorship(self):
        mentee = User.objects.get(email="mentee0@buddy.com")
        request = BuddyRequest.objects.get(requestor=mentee)
        c = Client()
        c.force_login(mentee)
        response = c.post(f"/complete/{request.id}", {"status": "complete",})
        assert response.status_code == 302
        request = BuddyRequest.objects.get(requestor=mentee)
        assert request.status == BuddyRequest.Status.COMPLETED

    def test_requestee_complete_mentorship(self):
        mentor = User.objects.get(email="mentor0@buddy.com")
        request = BuddyRequest.objects.get(requestee=mentor)
        c = Client()
        c.force_login(mentor)
        response = c.post(f"/complete/{request.id}", {"status": "complete",})
        assert response.status_code == 302
        request = BuddyRequest.objects.get(requestee=mentor)
        assert request.status == BuddyRequest.Status.COMPLETED
    
    def test_unauthorized_complete_mentorship(self):
        someone = User.objects.get(email="someone0@buddy.com")
        mentor = User.objects.get(email="mentor0@buddy.com")
        request = BuddyRequest.objects.get(requestee=mentor)
        c = Client()
        c.force_login(someone)
        response = c.post(f"/complete/{request.id}", {"status": "complete",})
        assert response.status_code == 403
        request = BuddyRequest.objects.get(requestee=mentor)
        assert request.status == BuddyRequest.Status.ACCEPTED


def create_test_users(
    n, handle, experiences, looking_for_mentors=True, looking_for_mentees=True
):
    """
    n: number of users to create \n
    handle: e.g. "mentor" to create "mentor0@buddy.com", "mentor1@buddy.com", etc. Also populates first name \n
    experiences: list of dictionaries with keys for skill (object), level, exp_type (takes enum)
    looking_for_mentors: defaults to True \n
    looking_for_mentees: defaults to True \n
    """

    users = []
    for i in range(n):
        users.append(
            User.objects.create_user(
                first_name=f"{handle}{i}",
                last_name="Buddy",
                email=f"{handle}{i}@buddy.com",
            )
        )

    for user in users:
        profile = Profile.objects.create(
            user=user,
            bio=f"I am {user.first_name} {user.last_name}.",
            looking_for_mentees=looking_for_mentees,
            looking_for_mentors=looking_for_mentors,
        )

        for exp in experiences:
            Experience.objects.create(
                profile=profile,
                skill=exp["skill"],
                level=exp["level"],
                exp_type=exp["exp_type"],
            )
    return users
