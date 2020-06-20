import os
from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.urls import reverse
from django.utils import timezone
from apps.users.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class BuddyRequest(models.Model):
    class Status(models.IntegerChoices):
        NEW = 0
        ACCEPTED = 1
        REJECTED = 2

    class RequestType(models.IntegerChoices):
        REQUEST = 0
        OFFER = 1

    request_type = models.IntegerField(choices=RequestType.choices, blank=False)
    status = models.IntegerField(choices=Status.choices, blank=False, default=0)
    request_sent = models.DateTimeField(default=timezone.now)
    requestee = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="requestee"
    )
    requestor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="requestor"
    )
    message = models.TextField()

    def __str__(self):
        request_type_str = ["Request", "Offer"][int(self.request_type)]
        return (
            f"{request_type_str} from "
            f"{self.requestor.email} to {self.requestee.email} on "
            f"{self.request_sent}"
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        request_type_str = ["Request", "Offer"][int(self.request_type)]
        if self.status == 0:
            profile = Profile.objects.get(user=self.requestor)
            profile_url = reverse("profile", args=[profile.id])
            request_detail_url = reverse("request_detail", args=[self.id])
            plain_message = "".join(
                [
                    f"{self.requestor.first_name} {self.requestor.last_name} ",
                    f"sent you a Buddy {request_type_str} ",
                    "with the following message: \n",
                    f"{self.message}",
                ]
            )
            html_message = "".join(
                [
                    f"<p><a href='{os.getenv('APP_URL')}{profile_url}'>",
                    f"{self.requestor.first_name} {self.requestor.last_name}</a> ",
                    f"sent you a <a href='{os.getenv('APP_URL')}{request_detail_url}''>",
                    f"Buddy {request_type_str}</a> ",
                    "with the following message:</p>",
                    f"{self.message}",
                ]
            )
            send_mail(
                f"{self.requestor.first_name} sent you a Buddy {request_type_str}",
                plain_message,
                settings.EMAIL_ADDRESS,
                [self.requestee.email],
                html_message=html_message,
            )
        elif self.status == 1:
            profile = Profile.objects.get(user=self.requestee)
            profile_url = reverse("profile", args=[profile.id])
            plain_message = "".join(
                [
                    f"{self.requestee.first_name} {self.requestee.last_name} ",
                    f"has accepted your Buddy {request_type_str} . Contact them at ",
                    f"{self.requestee.email} to begin your mentorship!",
                ]
            )
            html_message = "".join(
                [
                    f"<p><a href='{os.getenv('APP_URL')}{profile_url}'>",
                    f"{self.requestee.first_name} {self.requestee.last_name}</a> ",
                    f"has accepted your Buddy {request_type_str}. Contact them at ",
                    f"<a href='mailto:{self.requestee.email}'>",
                    f"{self.requestee.email}</a> to begin your mentorship!</p>",
                ]
            )
            send_mail(
                f"{self.requestee.first_name} accepted your "
                f"Buddy {request_type_str}",
                plain_message,
                settings.EMAIL_ADDRESS,
                [self.requestor.email],
                html_message=html_message,
            )
        elif self.status == 2:
            pass


class Profile(models.Model):
    """
    A model for storing user profile information
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bio = models.TextField()

    def __str__(self):
        return f"Profile for {self.user.email}"

    def get_short_bio(self):
        trunc_bio = self.bio[:240]
        first_nl = trunc_bio.find("\n")
        if first_nl > -1:
            return trunc_bio[:first_nl]
        if self.bio == trunc_bio:
            return trunc_bio
        last_dot = trunc_bio.rfind(".")
        last_bang = trunc_bio.rfind("!")
        last_huh = trunc_bio.rfind("?")
        last_sentence = max(last_dot, last_bang, last_huh)
        if last_sentence > -1:
            return trunc_bio[: last_sentence + 1]
        return trunc_bio[: trunc_bio.rfind(" ") + 1]

    def get_can_help(self):
        return Experience.objects.filter(
            profile=self, exp_type=Experience.Type.CAN_HELP
        ).order_by("-level", "skill__skill")

    def get_help_wanted(self):
        return Experience.objects.filter(
            profile=self, exp_type=Experience.Type.WANT_HELP
        ).order_by("level", "skill__skill")

    def get_top_can_help(self):
        return self.get_can_help()[:3]

    def get_top_help_wanted(self):
        return self.get_help_wanted()[:3]


class Skill(models.Model):
    """
    skill: lowercased name of skill (e.g. "python", "mvc", etc.). Must be unique.\n
    display_name: name showed in UI, e.g. "Python", "MVC", etc.
    """

    skill = models.CharField(max_length=30, unique=True)
    display_name = models.CharField(max_length=30, null=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.display_name = self.skill.title()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.skill


class Experience(models.Model):
    """
    Details an individual user's experience with a skill
    """

    class Type(models.IntegerChoices):
        WANT_HELP = 0
        CAN_HELP = 1

    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    level = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    exp_type = models.IntegerField(choices=Type.choices, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["skill", "profile"], name="unique_skill")
        ]

    def __str__(self):
        return f"{self.profile.user.email} {self.skill}"
