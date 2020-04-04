from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404

from buddy_mentorship.models import BuddyRequest


@login_required(login_url="login")
def requests_list(request):
    requests_sent = BuddyRequest.objects.filter(requestor=request.user)
    requests_received = BuddyRequest.objects.filter(requestee=request.user)
    context = {
        "requests_sent": requests_sent,
        "requests_received": requests_received,
        "title": "Requests",
    }
    return render(request, "users/requests.html", context)


@login_required(login_url="login")
def request_detail(request, request_id: int):
    buddy_request = get_object_or_404(BuddyRequest, pk=request_id)
    if not user_can_access_request(request.user, buddy_request):
        return HttpResponseForbidden("You do not have access to this request")
    context = {"buddy_request": buddy_request, "title": "Request Detail"}
    return render(request, "users/request.html", context)


def user_can_access_request(user, buddy_request) -> bool:
    return (
        user == buddy_request.requestee
        or user == buddy_request.requestor
        or user.is_staff
    ) and user.is_active
