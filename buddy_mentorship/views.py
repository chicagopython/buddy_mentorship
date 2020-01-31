from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    return render(request, "buddy_mentorship/home.html")
    return HttpResponse("Hello, world")
