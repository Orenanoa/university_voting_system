from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from .forms import (BallotForm, CandidateForm, ElectionForm, PositionForm,
                    StudentForm, VoterForm)
from .models import Ballot, Candidate, Election, Position, Student, Voter


# ---------- generic CRUD (Create / Read / Update / Delete) ----------
class ResourceMixin(LoginRequiredMixin):
    """Shared config. Subclasses are built by make_crud() below."""
    model = None
    resource = ""        # url prefix, e.g. "students"
    title = ""           # page heading
    columns = []         # [(header, function(obj) -> value)]
    success_url = None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(resource=self.resource, title=self.title, active=self.resource)
        return ctx


class ResourceList(ResourceMixin, CreateView):
    """READ (the table) and CREATE (the form above it) on one page."""
    template_name = "crud/list.html"

    def get_queryset(self):
        return self.model.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["headers"] = [h for h, _ in self.columns]
        ctx["rows"] = [(o, [fn(o) for _, fn in self.columns]) for o in self.get_queryset()]
        ctx["extra_actions"] = self.resource == "elections"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f"{self.title}: saved.")
        return super().form_valid(form)


class ResourceUpdate(ResourceMixin, UpdateView):
    template_name = "crud/form.html"

    def form_valid(self, form):
        messages.success(self.request, "Changes saved.")
        return super().form_valid(form)


class ResourceDelete(ResourceMixin, DeleteView):
    template_name = "crud/confirm_delete.html"

    def form_valid(self, form):
        messages.success(self.request, "Deleted.")
        return super().form_valid(form)


def make_crud(model, form_class, resource, title, columns):
    url = reverse_lazy(f"{resource}-list")
    attrs = dict(model=model, form_class=form_class, resource=resource, title=title,
                 columns=columns, success_url=url)
    del_attrs = {k: v for k, v in attrs.items() if k != "form_class"}  # DeleteView uses its own form
    return (type(f"{model.__name__}List", (ResourceList,), attrs),
            type(f"{model.__name__}Update", (ResourceUpdate,), attrs),
            type(f"{model.__name__}Delete", (ResourceDelete,), del_attrs))


class ElectionList(ResourceList):
    def get_queryset(self):
        return Election.objects.annotate(voter_count=Count("voters"))


StudentList, StudentUpdate, StudentDelete = make_crud(
    Student, StudentForm, "students", "Register Student",
    [("Student ID", lambda o: o.student_id), ("First Name", lambda o: o.first_name),
     ("Last Name", lambda o: o.last_name), ("Gender", lambda o: o.gender),
     ("Course", lambda o: o.course), ("Year of Study", lambda o: o.year),
     ("Session", lambda o: o.session)])

_ElList, ElectionUpdate, ElectionDelete = make_crud(
    Election, ElectionForm, "elections", "Election",
    [("Election ID", lambda o: o.pk), ("Title", lambda o: o.title),
     ("Voters (registered)", lambda o: o.voter_count if hasattr(o, "voter_count") else o.voters.count()),
     ("Status", lambda o: o.status)])
ElectionList = type("ElectionList", (ElectionList, _ElList), {})

PositionList, PositionUpdate, PositionDelete = make_crud(
    Position, PositionForm, "positions", "Position",
    [("ID", lambda o: o.pk), ("Election", lambda o: o.election.title),
     ("Title", lambda o: o.title), ("Description", lambda o: o.description)])

CandidateList, CandidateUpdate, CandidateDelete = make_crud(
    Candidate, CandidateForm, "candidates", "Candidate",
    [("ID", lambda o: o.pk), ("Student", lambda o: o.student.name),
     ("Position", lambda o: o.position.title), ("Election", lambda o: o.position.election.title),
     ("Votes", lambda o: o.votes)])

VoterList, VoterUpdate, VoterDelete = make_crud(
    Voter, VoterForm, "voters", "Voter",
    [("Voter ID", lambda o: f"V{o.pk}"), ("Election", lambda o: o.election.title),
     ("Student", lambda o: o.student.name), ("Age", lambda o: o.age),
     ("Status", lambda o: o.status)])


class ElectionStatus(LoginRequiredMixin, View):
    def post(self, request, pk, status):
        election = get_object_or_404(Election, pk=pk)
        if status not in ("Pending", "Ongoing", "Ended"):
            messages.error(request, "Invalid status.")
        else:
            election.status = status
            election.save()
            messages.success(request, f"'{election.title}' is now {status}.")
        return redirect("elections-list")


# ---------- pages ----------
class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(active="home", **kwargs)


class BallotView(LoginRequiredMixin, View):
    """Pick an ongoing election (GET ?election=), then submit the ballot (POST)."""

    def get(self, request):
        election = Election.objects.filter(pk=request.GET.get("election") or 0, status="Ongoing").first()
        form = BallotForm(election) if election else None
        return self.page(request, election, form)

    def post(self, request):
        election = get_object_or_404(Election, pk=request.POST.get("election") or 0)
        form = BallotForm(election, request.POST)
        if form.is_valid():
            try:
                form.save()
            except ValidationError as e:
                form.add_error(None, e)
            else:
                messages.success(request, "Ballot submitted successfully. Thank you for voting.")
                return redirect(f"{request.path}?election={election.pk}")
        return self.page(request, election, form)

    def page(self, request, election, form):
        ballots = Ballot.objects.select_related("election", "position", "candidate__student")
        return render(request, "ballot.html", dict(
            active="ballot", elections=Election.objects.filter(status="Ongoing"),
            election=election, form=form, ballots=ballots))
