from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect

from apps.users.models import User

from .models import BuddyRequest, Profile

def index(request):
    return render(request, "buddy_mentorship/home.html")


@login_required(login_url="login")
def profile(request, profile_uuid):
    profile = Profile.user.get(uuid=profile_uuid)
    context = {'can_request': can_request(request.user, requestee), 'profile': profile}
    return render(request, "buddy_mentorship/profile.html", context)

def send_request(request, uuid):
    user = request.user
    requestee = User.objects.get(uuid=uuid)
    if can_request(user, requestee):
        BuddyRequest.objects.create(
            requestor=user, requestee=requestee, message="Hi! Will you be my mentor?"
        )
        return redirect('requests')
    return HttpResponseForbidden("You cannot send this user a request")

# should not always return true, but also we need to build the profile model
def can_request(requestor, requestee):
    return False