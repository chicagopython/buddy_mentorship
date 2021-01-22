from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.db.models import OuterRef, Subquery
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.views.generic.edit import DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView

from apps.users.models import User

from .forms import ProfileEditForm, SkillForm
from .models import BuddyRequest, Profile, Experience, Skill

import urllib.parse


def index(request):
    return render(request, "buddy_mentorship/home.html", {"active_page": "home"})


@login_required(login_url="login")
def profile(request, profile_id=""):
    user = request.user
    user_profile = Profile.objects.filter(user=user).first()
    if not profile_id:
        profile = user_profile
        profile_id = profile.id if profile else None
    if profile_id is None:
        return redirect("edit_profile")
    profile = get_object_or_404(Profile, id=profile_id)
    existing_request_to_user = None
    existing_offer_to_user = None
    existing_request_from_user = None
    existing_offer_from_user = None
    if user_profile != profile and user_profile != None:
        existing_request_from_user = BuddyRequest.objects.find_by_users(
            requestor=user_profile.user,
            requestee=profile.user,
            request_type=BuddyRequest.RequestType.REQUEST,
        )
        existing_offer_to_user = BuddyRequest.objects.find_by_users(
            requestor=profile.user,
            requestee=user_profile.user,
            request_type=BuddyRequest.RequestType.OFFER,
        )
        existing_offer_from_user = BuddyRequest.objects.find_by_users(
            requestor=user_profile.user,
            requestee=profile.user,
            request_type=BuddyRequest.RequestType.OFFER,
        )
        existing_request_to_user = BuddyRequest.objects.find_by_users(
            requestor=profile.user,
            requestee=user_profile.user,
            request_type=BuddyRequest.RequestType.REQUEST,
        )

    can_request = can_request_as_mentor(request.user, profile.user)
    can_offer = can_offer_to_mentor(request.user, profile.user)
    context = {
        "existing_request_to_user": existing_request_to_user,
        "existing_offer_to_user": existing_offer_to_user,
        "existing_request_from_user": existing_request_from_user,
        "existing_offer_from_user": existing_offer_from_user,
        "can_request": can_request,
        "can_offer": can_offer,
        "cannot_request_not_looking": (
            not can_request
            and not existing_request_from_user
            and not existing_offer_to_user
            and user != user_profile
            and not profile.looking_for_mentees
        ),
        "cannot_offer_not_looking": (
            not can_offer
            and not existing_request_to_user
            and not existing_offer_from_user
            and user != user_profile
            and not profile.looking_for_mentors
        ),
        "cannot_request_no_skills": (
            not can_request
            and not existing_request_from_user
            and not existing_offer_to_user
            and user != user_profile
            and profile.looking_for_mentees
        ),
        "cannot_offer_no_skills": (
            not can_offer
            and not existing_request_to_user
            and not existing_offer_from_user
            and user != user_profile
            and profile.looking_for_mentors
        ),
        "profile": profile,
        "user_profile": user_profile,
        "active_page": "profile",
        "request_type": BuddyRequest.RequestType,
        "exp_types": Experience.Type,
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
    ) and can_request_as_mentor(user, requestee)

    can_send_offer = int(request_type) == int(
        BuddyRequest.RequestType.OFFER
    ) and can_offer_to_mentor(user, requestee)

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
def can_request_as_mentor(mentee, mentor):
    mentee_profile = Profile.objects.filter(user=mentee).first()
    mentor_profile = Profile.objects.filter(user=mentor).first()

    if (not mentee_profile) or (not mentor_profile):
        return False

    return (
        mentee != mentor
        and mentee.is_active
        and mentor.is_active
        and required_experiences(mentee, mentor)
        and mentor_profile.looking_for_mentees
        and not existing_requests(mentee, mentor)
    )


def can_offer_to_mentor(mentor, mentee):
    mentor_profile = Profile.objects.filter(user=mentor).first()
    mentee_profile = Profile.objects.filter(user=mentee).first()

    if (not mentor_profile) or (not mentee_profile):
        return False

    return (
        mentor != mentee
        and mentor.is_active
        and mentee.is_active
        and required_experiences(mentee, mentor)
        and mentee_profile.looking_for_mentors
        and not existing_requests(mentee, mentor)
    )


# helper function for can_request_as_mentor and can_offer_to_mentor
# checks if there are existing requests for a specific mentor/mentee pair, regardless of who initiated
def existing_requests(mentee, mentor):
    existing_requests = BuddyRequest.objects.filter(
        requestor=mentee,
        requestee=mentor,
        request_type=BuddyRequest.RequestType.REQUEST,
    )
    existing_offers = BuddyRequest.objects.filter(
        requestor=mentor, requestee=mentee, request_type=BuddyRequest.RequestType.OFFER,
    )
    return existing_requests or existing_offers


# helper function for can_request_as_mentor and can_offer_to_mentor
# checks mentee has skills they want help with and mentor has skills they need help with
def required_experiences(mentee, mentor):
    mentee_experiences = Experience.objects.filter(profile__user=mentee).all()
    mentor_experiences = Experience.objects.filter(profile__user=mentor).all()
    return any(
        [
            experience.exp_type == Experience.Type.WANT_HELP
            for experience in mentee_experiences
        ]
    ) and any(
        [
            experience.exp_type == Experience.Type.CAN_HELP
            for experience in mentor_experiences
        ]
    )


@login_required(login_url="login")
def skill_search(request):
    term = request.GET.get("term", None)

    skills = Skill.objects.filter(skill__icontains=term)
    return JsonResponse([skill.display_name for skill in skills], safe=False)


class AddSkill(LoginRequiredMixin, FormView):
    login_url = "login"
    template_name = "buddy_mentorship/add_skill.html"
    form_class = SkillForm
    success_url = "/profile"

    def get_context_data(self, **kwargs):
        context = super(AddSkill, self).get_context_data(**kwargs)
        context["exp_type"] = self.kwargs["exp_type"]
        return context

    def form_valid(self, form: SkillForm):
        user = self.request.user
        profile = Profile.objects.get(user=user)
        exp_type = form.cleaned_data.get("exp_type")
        skill = form.cleaned_data.get("skill").lower()
        level = form.cleaned_data.get("level")

        existing_skill = Skill.objects.filter(skill=skill).first()
        if existing_skill is None:
            existing_skill = Skill.objects.create(skill=skill, display_name=skill)

        existing_experience = Experience.objects.filter(
            skill=existing_skill, profile=profile
        ).first()
        if existing_experience is None:
            existing_experience = Experience.objects.create(
                skill=existing_skill, profile=profile, level=1, exp_type=exp_type,
            )
            existing_experience.level = level
            existing_experience.exp_type = exp_type
            existing_experience.save()
        else:
            return redirect(f"/edit_skill/{existing_experience.id}")

        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


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
        context["looking_for_mentors"] = (
            profile.looking_for_mentors if profile else True
        )
        context["looking_for_mentees"] = (
            profile.looking_for_mentees if profile else True
        )
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
        profile.looking_for_mentors = form.cleaned_data.get("looking_for_mentors")
        profile.looking_for_mentees = form.cleaned_data.get("looking_for_mentees")
        profile.save()


class UpdateExperience(LoginRequiredMixin, UpdateView):
    login_url = "login"
    model = Experience
    fields = ["exp_type", "level"]
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


@login_required(login_url="login")
def complete_mentorship(request, buddy_request_id):
    buddy_request = BuddyRequest.objects.get(id=buddy_request_id)
    if (
        request.user != buddy_request.requestee
        and request.user != buddy_request.requestor
    ):
        return HttpResponseForbidden("You cannot mark this mentorship complete.")
    if request.method != "POST":
        return HttpResponseForbidden("Error - page accessed incorrectly")
    if request.POST["status"] == "complete":
        buddy_request.status = 3
    buddy_request.save()
    return redirect("request_detail", request_id=buddy_request_id)


class Search(LoginRequiredMixin, ListView):
    login_url = "login"

    template_name = "buddy_mentorship/search.html"

    paginate_by = 5

    queryset = Profile.objects.all().order_by("-id")

    def get_queryset(self):

        search_type = self.request.GET.get("type", "mentor")
        if search_type == "mentee":
            all_qualified = self.queryset.filter(
                experience__exp_type=Experience.Type.WANT_HELP, looking_for_mentors=True
            ).exclude(user=self.request.user)
        if search_type == "mentor":
            all_qualified = self.queryset.filter(
                experience__exp_type=Experience.Type.CAN_HELP, looking_for_mentees=True
            ).exclude(user=self.request.user)

        query_text = self.request.GET.get("q", "")
        if query_text is not "":
            search_vector = SearchVector(
                "user__first_name",
                "user__last_name",
                "bio",
                "experience__skill__skill",
            )
            search_query = SearchQuery(
                query_text.replace(" ", " | "), search_type="raw"
            )
            search_results = (
                all_qualified.annotate(
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
            search_results = all_qualified.distinct("id")
        return search_results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "search"
        context["search_type"] = self.request.GET.get("type", "mentor")

        query_text = self.request.GET.get("q", "")
        context["query_text"] = query_text
        quoted_query_text = urllib.parse.quote_plus(query_text)

        results = []
        for profile in context["page_obj"].object_list:
            result = {}
            result["profile"] = profile
            result["can_help"] = profile.get_top_can_help(query_text)
            result["want_help"] = profile.get_top_want_help(query_text)
            results.append(result)
        context["results"] = results

        profile = Profile.objects.filter(user=self.request.user).first()
        context["looking_for_mentors"] = (
            profile.looking_for_mentors if profile else False
        )
        context["looking_for_mentees"] = (
            profile.looking_for_mentees if profile else False
        )

        if context["page_obj"].has_previous():
            context[
                "first_page_url"
            ] = f"?q={ quoted_query_text }&type={ context['search_type'] }&page=1"
            context["prev_page_url"] = (
                f"?q={ quoted_query_text }&type={ context['search_type'] }"
                f"&page={ context['page_obj'].previous_page_number()}"
            )
        if context["page_obj"].has_next():
            context["next_page_url"] = (
                f"?q={ quoted_query_text }&type={ context['search_type'] }"
                f"&page={ context['page_obj'].next_page_number()}"
            )
            context[
                "last_page_url"
            ] = f"?q={ quoted_query_text }&type={ context['search_type'] }&page=last"

        return context
