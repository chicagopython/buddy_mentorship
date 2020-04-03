from django.core.mail import send_mail
from django.db import models
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
            send_mail(
                f"{self.requestor.first_name} sent you a " 
                "BuddyRequest",
                self.message,
                self.requestor.email,
                [self.requestee.email],
            )
        elif self.status == 1:
            send_mail(
                f"{self.requestee.first_name} accepted your " 
                "BuddyRequest",
                self.message,
                self.requestee.email,
                [self.requestor.email],
            )


class Profile(models.Model):
    """
    A model for storing user profile information
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bio = models.TextField()
    help_wanted = models.BooleanField(default=False)
    can_help = models.BooleanField(default=False)

    def __str__(self):
        return self.bio
