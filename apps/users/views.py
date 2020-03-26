from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404

from buddy_mentorship.models import BuddyRequest


@login_required(login_url="login")
def requests_list(request):
    requests_sent = [
        {
            "to": "Ben",
            "message": "Hi, I would like your help with some python",
            "id": 1,
        },
        {
            "to": "Jake",
            "message": "Hi, I would like your help with some javascript",
            "id": 2,
        },
    ]
    requests_received = [
        {
            "from": "James",
            "message": "Hi, I've been learning some python. Are you free to help my learn more?",
            "id": 3,
        }
    ]
    context = {"requests_sent": requests_sent, "requests_received": requests_received, "active_page": "requests"}
    return render(request, "users/requests.html", context)


@login_required(login_url="login")
def request_detail(request, request_id: int):
    buddy_request = get_object_or_404(BuddyRequest, pk=request_id)
    if not user_can_access_request(request.user, buddy_request):
        return HttpResponseForbidden("You do not have access to this request")
    return render(
        request, 
        "users/request.html", 
        {'buddy_request': buddy_request}
    )


def user_can_access_request(user, buddy_request) -> bool:
    return (
        user.id == buddy_request.requestee
        or user.id == buddy_request.requestor
        or user.is_staff
    ) and user.is_active
