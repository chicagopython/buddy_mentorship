from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    return render(request, "buddy_mentorship/home.html")


@login_required(login_url="login")
def profile(request):
    return render(request, "buddy_mentorship/profile.html")
