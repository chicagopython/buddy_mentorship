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
from django.urls import reverse
from django.utils import timezone

from .models import BuddyRequest, Profile, Skill, Experience
from .views import can_request, send_request

from apps.users.models import User

from django.db import IntegrityError


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
            user=user, bio="i'm super interested in Python"
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
        response = c.get(f"/profile/",)
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

        assert list(profile.get_top_help_wanted()) == exps[:3]

        assert list(profile.get_top_can_help()) == exps[4:7]


class SendBuddyRequestTest(TestCase):
    def setUp(self):

        skill1, skill2 = (
            Skill.objects.create(skill="pandas"),
            Skill.objects.create(skill="Flask"),
        )

        mentor = User.objects.create_user(
            first_name="Frank", last_name="Mackey", email="mentor@user.com"
        )

        mentor_profile = Profile.objects.create(
            user=mentor, bio="Experienced Undercover detective."
        )

        Experience.objects.create(
            profile=mentor_profile,
            skill=skill1,
            level=2,
            exp_type=Experience.Type.CAN_HELP,
        )

        mentee = User.objects.create_user(
            first_name="Cassie", last_name="Maddox", email="mentee@user.com"
        )

        mentee_profile = Profile.objects.create(
            user=mentee, bio="Aspiring Undercover detective with background in Murder."
        )

        Experience.objects.create(
            profile=mentee_profile,
            skill=skill1,
            level=3,
            exp_type=Experience.Type.WANT_HELP,
        )

        someone = User.objects.create_user(
            first_name="Rob", last_name="Ryan", email="someone@user.com"
        )

        someone_profile = Profile.objects.create(
            user=someone, bio="You ever see somebody ruin their own life?"
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
            message="Please help me!",
            request_type=BuddyRequest.RequestType.REQUEST,
        )
        assert not can_request(mentee, someone)
        assert not can_request(someone, mentor)
        assert not can_request(mentee, mentor)
        buddy_request.delete()

    def test_send_request(self):
        c = Client()
        mentee = User.objects.get(email="mentee@user.com")
        mentor = User.objects.get(email="mentor@user.com")
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
        assert mail.outbox[0].subject == "Cassie sent you a Buddy Request"
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
        mentee = User.objects.get(email="mentee@user.com")
        mentor = User.objects.get(email="mentor@user.com")
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
        assert mail.outbox[1].subject == "Frank accepted your Buddy Request"
        profile_link = f"<a href='{os.getenv('APP_URL')}{reverse('profile',args=[mentor_profile.id])}'>"
        mentor_name = f"{mentor.first_name} {mentor.last_name}"
        sent_message = mail.outbox[1].alternatives[0][0]
        assert profile_link in sent_message
        assert mentor_name in sent_message
        assert mentee.email in mail.outbox[1].recipients()

    def test_reject_request(self):
        c = Client()
        mentee = User.objects.get(email="mentee@user.com")
        mentor = User.objects.get(email="mentor@user.com")
        mentor_profile = Profile.objects.get(user=mentor)
        buddy_request = BuddyRequest.objects.create(
            requestor=mentee,
            requestee=mentor,
            request_type=BuddyRequest.RequestType.REQUEST,
        )
        buddy_request.status = 2
        buddy_request.save()

        # right now this doesn't do anything
        assert len(mail.outbox) == 1


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
        assert mail.outbox[0].subject == "mentor0 sent you a Buddy Offer"
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
        assert mail.outbox[1].subject == "mentee0 accepted your Buddy Offer"
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
            },
        )
        user.refresh_from_db()
        assert user.first_name == "new name"
        assert user.last_name == "new last name"
        assert user.email == "newemail@example.com"
        profile = Profile.objects.get(user=user)
        assert profile.bio == "predicting the future"

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
            },
        )
        profile = Profile.objects.get(user=user)
        assert profile.bio == "predicting the future"


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

        profile_user = Profile.objects.create(user=user, bio="")

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
            user=mentor1, bio="Father, country gentleman. Friend of the Lucas family."
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
        )

        Experience.objects.create(
            profile=profile_mentor2,
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
        )

        create_test_users(
            1,
            "mentee1",
            [{"skill": skill1, "level": 1, "exp_type": Experience.Type.WANT_HELP},],
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


class SkillTest(TestCase):
    def setUp(self):
        create_test_users(1, "user", [])

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


def create_test_users(n, handle, experiences):
    """
    n: number of users to create \n
    handle: e.g. "mentor" to create "mentor0@buddy.com", "mentor1@buddy.com", etc. Also populates first name \n
    experiences: list of dictionaries with keys for skill (object), level, exp_type (takes enum)
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
            user=user, bio=f"I am {user.first_name} {user.last_name}."
        )

        for exp in experiences:
            Experience.objects.create(
                profile=profile,
                skill=exp["skill"],
                level=exp["level"],
                exp_type=exp["exp_type"],
            )
    return users
