from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView

from apps.users.models import User

from .forms import ProfileEditForm
from .models import BuddyRequest, Profile, Experience


def index(request):
    return render(request, "buddy_mentorship/home.html", {"active_page": "home"})


@login_required(login_url="login")
def profile(request, profile_id=""):
    if not profile_id:
        user = request.user
        profile = Profile.objects.filter(user=user).first()
        profile_id = profile.id if profile else None
    if profile_id is None:
        return redirect("edit_profile")
    profile = Profile.objects.get(id=profile_id)
    context = {
        "can_request": can_request(request.user, profile.user),
        "profile": profile,
        "active_page": "profile",
    }
    return render(request, "buddy_mentorship/profile.html", context)


@login_required(login_url="login")
def send_request(request, uuid):
    user = request.user
    requestee = User.objects.get(uuid=uuid)
    if request.method != "POST":
        return HttpResponseForbidden("Error - page accessed incorrectly")
    message = request.POST["message"]
    if can_request(user, requestee):
        BuddyRequest.objects.create(
            requestor=user, requestee=requestee, message=message
        )
        return redirect("requests")
    return HttpResponseForbidden("You cannot send this user a request")


# needs to be updated as we expand profile model
def can_request(requestor, requestee):
    requestor_profile = Profile.objects.get(user=requestor)
    requestee_profile = Profile.objects.get(user=requestee)
    requestor_experiences = Experience.objects.filter(profile=requestor_profile).all()
    requestee_experiences = Experience.objects.filter(profile=requestee_profile).all()


    # when possible, should be no pending existing requests
    existing_requests = BuddyRequest.objects.filter(
        requestor=requestor, requestee=requestee
    )

    return (
        requestor != requestee
        and any([experience.help_wanted for experience in requestor_experiences])
        and any([experience.can_help for experience in requestee_experiences])
        and requestor.is_active
        and requestee.is_active
        and not existing_requests
    )


@login_required(login_url="login")
def update_request(request, buddy_request_id):
    buddy_request = BuddyRequest.objects.get(id=buddy_request_id)
    if request.user != buddy_request.requestor:
        return HttpResponseForbidden("You cannot accept or reject this request")
    if request.method != "POST":
        return HttpResponseForbidden("Error - page accessed incorrectly")
    if request.POST["status"] == "accept":
        buddy_request.status = 1
    if request.POST["status"] == "ignore":
        buddy_request.status = 2
    buddy_request.save()
    return redirect("request_detail", request_id=buddy_request_id)


class ProfileEdit(LoginRequiredMixin, FormView):
    login_url = "login"

    template_name = "buddy_mentorship/edit_profile.html"
    form_class = ProfileEditForm
    success_url = "/profile/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile = Profile.objects.filter(user=self.request.user).first()

        context["first_name"] = user.first_name
        context["last_name"] = user.last_name
        context["bio"] = profile.bio if profile else ""
        context["email"] = user.email

        return context

    def form_valid(self, form: ProfileEditForm):
        self.update_user(form)
        self.upsert_profile(form)

        return super().form_valid(form)

    def update_user(self, form: ProfileEditForm):
        user = self.request.user
        user.first_name = form.cleaned_data.get("first_name")
        user.last_name = form.cleaned_data.get("last_name")
        user.email = form.cleaned_data.get("email")

        user.save()

    def upsert_profile(self, form: ProfileEditForm):

        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        profile.bio = form.cleaned_data.get("bio")
        profile.can_help = form.cleaned_data.get("can_help")
        profile.help_wanted = form.cleaned_data.get("help_wanted")
        profile.save()


class Search(LoginRequiredMixin, ListView):
    login_url = "login"

    template_name = "buddy_mentorship/search.html"

    paginate_by = 5

    queryset = Profile.objects.all().order_by("-id")

    def get_queryset(self):
        all_mentors = self.queryset.filter(experience__can_help=True)
        search_results = all_mentors.exclude(user=self.request.user)

        query_text = self.request.GET.get("q", None)
        if query_text is not None:
            if query_text is not "":
                search_vector = SearchVector(
                    "user__first_name", "user__last_name", "bio",
                )
                search_query = SearchQuery(query_text, search_type="plain")
                search_results = search_results.annotate(search=search_vector).filter(
                    search=search_query
                )
                search_results = search_results.annotate(
                    rank=SearchRank(search_vector, search_query)
                ).order_by("-rank")
        return search_results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "search"
        context["query_text"] = self.request.GET.get("q", None)
        return context