from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render


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
    if not user_can_access_request(request.user, None):
        return HttpResponseForbidden("You do not have access to this request")
    context = {
        "requestee": "John",
        "requestor": "Jacob",
        "message": "I'm learning Python.",
    }
    return render(request, "users/request.html", context)


def user_can_access_request(user, buddy_request) -> bool:
    # TODO: when we have a request model, remove this escape
    if buddy_request is None:
        return True
    if user.id == buddy_request.requestee or user.id == buddy_request.requestor:
        return True
    return False
