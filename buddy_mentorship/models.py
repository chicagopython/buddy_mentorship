from django.db import models
from django.utils import timezone
from apps.users.models import User

class BuddyRequest(models.Model):
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
        last_dot = trunc_bio.rfind(".")
        last_bang = trunc_bio.rfind("!")
        last_huh = trunc_bio.rfind("?")
        last_sentence = max(last_dot, last_bang, last_huh)
        if last_sentence > -1:
            return trunc_bio[:last_sentence+1]
        return trunc_bio[:trunc_bio.rfind(" ")+1]