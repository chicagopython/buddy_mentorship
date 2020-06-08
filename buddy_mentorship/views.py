from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.db.models import OuterRef, Subquery
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.views.generic.edit import DeleteView, UpdateView
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
        "can_offer": can_request(profile.user, request.user),
        "profile": profile,
        "active_page": "profile",
        "request_type": BuddyRequest.RequestType,
    }
    return render(request, "buddy_mentorship/profile.html", context)


@login_required(login_url="login")
def send_request(request, uuid):
    user = request.user
    requestee = User.objects.get(uuid=uuid)
    if request.method != "POST":
        return HttpResponseForbidden("Error - page accessed incorrectly")
    message = request.POST["message"]
    request_type = request.POST["request_type"]

    can_send_request = int(request_type) == int(
        BuddyRequest.RequestType.REQUEST
    ) and can_request(user, requestee)

    can_send_offer = int(request_type) == int(
        BuddyRequest.RequestType.OFFER
    ) and can_request(requestee, user)

    if can_send_request or can_send_offer:
        BuddyRequest.objects.create(
            requestor=user,
            requestee=requestee,
            message=message,
            request_type=request_type,
        )
        return redirect("requests")

    if int(request_type) == int(BuddyRequest.RequestType.REQUEST):
        return HttpResponseForbidden(f"You cannot send this user a request.")
    if int(request_type) == int(BuddyRequest.RequestType.OFFER):
        return HttpResponseForbidden(f"You cannot send this user an offer.")


# needs to be updated as we expand profile model
def can_request(requestor, requestee):
    requestor_profile = Profile.objects.get(user=requestor)
    requestee_profile = Profile.objects.get(user=requestee)

    requestor_experiences = Experience.objects.filter(profile=requestor_profile).all()
    requestee_experiences = Experience.objects.filter(profile=requestee_profile).all()

    existing_requests = BuddyRequest.objects.filter(
        requestor=requestor,
        requestee=requestee,
        request_type=BuddyRequest.RequestType.REQUEST,
    )
    existing_offers = BuddyRequest.objects.filter(
        requestor=requestee,
        requestee=requestor,
        request_type=BuddyRequest.RequestType.OFFER,
    )

    return (
        requestor != requestee
        and any([experience.help_wanted for experience in requestor_experiences])
        and any([experience.can_help for experience in requestee_experiences])
        and requestor.is_active
        and requestee.is_active
        and not existing_requests
        and not existing_offers
    )


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


class UpdateExperience(LoginRequiredMixin, UpdateView):
    login_url = "login"
    model = Experience
    fields = ["can_help", "help_wanted", "level"]
    success_url = "/profile/"

    def dispatch(self, request, *args, **kwargs):
        if request.user != self.get_object().profile.user:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class DeleteExperience(LoginRequiredMixin, DeleteView):
    login_url = "login"
    model = Experience
    success_url = "/profile/"

    def dispatch(self, request, *args, **kwargs):
        if request.user != self.get_object().profile.user:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


@login_required(login_url="login")
def update_request(request, buddy_request_id):
    buddy_request = BuddyRequest.objects.get(id=buddy_request_id)
    if request.user != buddy_request.requestee:
        return HttpResponseForbidden("You cannot accept or reject this request")
    if request.method != "POST":
        return HttpResponseForbidden("Error - page accessed incorrectly")
    if request.POST["status"] == "accept":
        buddy_request.status = 1
    if request.POST["status"] == "ignore":
        buddy_request.status = 2
    buddy_request.save()
    return redirect("request_detail", request_id=buddy_request_id)


class Search(LoginRequiredMixin, ListView):
    login_url = "login"

    template_name = "buddy_mentorship/search.html"

    paginate_by = 5

    queryset = Profile.objects.all().order_by("-id")

    def get_queryset(self):
        all_mentors = self.queryset.filter(experience__can_help=True).exclude(
            user=self.request.user
        )
        # needs to be distinct

        query_text = self.request.GET.get("q", None)
        if query_text is not None and query_text is not "":
            search_vector = SearchVector(
                "user__first_name",
                "user__last_name",
                "bio",
                "experience__skill__skill",
            )
            search_query = SearchQuery(query_text, search_type="plain")
            search_results = (
                all_mentors.annotate(
                    search=search_vector, rank=SearchRank(search_vector, search_query),
                )
                .filter(search=search_query, id=OuterRef("id"))
                .distinct("id")
            )

            ranked = (
                Profile.objects.annotate(rank=Subquery(search_results.values("rank")))
                .filter(id__in=Subquery(search_results.values("id")))
                .order_by("-rank")
            )

            search_results = ranked
        else:
            search_results = all_mentors.distinct("id")
        return search_results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "search"
        context["query_text"] = self.request.GET.get("q", None)
        return context
