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
