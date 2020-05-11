import os
from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.urls import reverse
from django.utils import timezone
from apps.users.models import User

class BuddyRequest(models.Model):
    class Status(models.IntegerChoices):
        NEW = 0
        ACCEPTED = 1
        REJECTED = 2

    status = models.IntegerField(
                        choices=Status.choices, 
                        blank=False, 
                        default=0
    )
    request_sent = models.DateTimeField(default=timezone.now)
    requestee = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="requestee"
    )
    requestor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="requestor"
    )
    message = models.TextField()

    def __str__(self):
        return (
            "Buddy request from "
            f"{self.requestor.email} to {self.requestee.email} on "
            f"{self.request_sent}"
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status == 0:
            profile = Profile.objects.get(user=self.requestor)
            profile_url = reverse('profile', args=[profile.id])
            plain_message = "".join([
                f"{self.requestor.first_name} {self.requestor.last_name} ",
                "sent you a Buddy Request with the following message: \n",
                f"{self.message}"
            ])
            html_message = "".join([
                f"<p><a href='{os.getenv('APP_URL')}{profile_url}'>",
                f"{self.requestor.first_name} {self.requestor.last_name}</a> ",
                f"sent you a Buddy Request ",
                "with the following message:</p>",
                f"{self.message}"
            ])
            send_mail(
                f"{self.requestor.first_name} sent you a " 
                "Buddy Request",
                plain_message,
                settings.EMAIL_ADDRESS,
                [self.requestee.email],
                html_message=html_message
            )
        elif self.status == 1:
            profile = Profile.objects.get(user=self.requestee)
            profile_url = reverse('profile', args=[profile.id])
            plain_message = "".join([
                f"{self.requestee.first_name} {self.requestee.last_name} ",
                "has accepted your Buddy Request. Contact them at ",
                f"{self.requestee.email} to begin your mentorship!"
            ])
            html_message = "".join([
                f"<p><a href='{os.getenv('APP_URL')}{profile_url}'>",
                f"{self.requestee.first_name} {self.requestor.last_name}</a> ",
                f"has accepted your Buddy Request. Contact them at ",
                f"<a href='mailto:{self.requestee.email}'>",
                f"{self.requestee.email}</a> to begin your mentorship!</p>"
            ])
            send_mail(
                f"{self.requestee.first_name} accepted your " 
                "Buddy Request",
                plain_message,
                settings.EMAIL_ADDRESS,
                [self.requestor.email],
                html_message=html_message
            )
        elif self.status == 2:
            # rejection email
            pass


class Profile(models.Model):
    """
    A model for storing user profile information
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bio = models.TextField()
    help_wanted = models.BooleanField(default=False)
    can_help = models.BooleanField(default=False)

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
            return trunc_bio[:last_sentence+1]
        return trunc_bio[:trunc_bio.rfind(" ")+1]