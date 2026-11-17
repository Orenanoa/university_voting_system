import json

from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Ballot, Candidate, Election, Position, Student, Voter


# ---------- serializers (the keys also match what the forms send) ----------
def ser_student(o):
    return dict(id=o.pk, student_id=o.student_id, first_name=o.first_name, last_name=o.last_name,
                gender=o.gender, course=o.course, year=o.year, session=o.session, name=o.name)


def ser_election(o):
    return dict(id=o.pk, title=o.title, status=o.status, voters=o.voters.count())


def ser_position(o):
    return dict(id=o.pk, election_id=o.election_id, election_title=o.election.title,
                title=o.title, description=o.description)


def ser_candidate(o):
    return dict(id=o.pk, student_id=o.student_id, student_name=o.student.name,
                position_id=o.position_id, position_title=o.position.title,
                election_title=o.position.election.title, votes=o.votes)


def ser_voter(o):
    return dict(id=o.pk, election_id=o.election_id, election_title=o.election.title,
                student_id=o.student_id, student_name=o.student.name, age=o.age, status=o.status)


RESOURCES = {
    "student": dict(model=Student, ser=ser_student,
                    keys=["student_id", "first_name", "last_name", "gender", "course", "year", "session"]),
    "election": dict(model=Election, ser=ser_election, keys=["title", "status"]),
    "position": dict(model=Position, ser=ser_position, keys=["election_id", "title", "description"]),
    "candidate": dict(model=Candidate, ser=ser_candidate, keys=["student_id", "position_id"]),
    "voter": dict(model=Voter, ser=ser_voter, keys=["election_id", "student_id", "age"]),
}


# ---------- helpers ----------
def err(message, status=400):
    return JsonResponse({"error": message}, status=status)


def body(request):
    try:
        data = json.loads(request.body or "{}")
        return data if isinstance(data, dict) else {}
    except ValueError:
        return {}


def unauth():
    return err("Please log in.", 401)


# ---------- auth ----------
@require_http_methods(["POST"])
def login_view(request):
    data = body(request)
    user = authenticate(request, username=str(data.get("username", "")).strip(),
                        password=str(data.get("password", "")))
    if user is None:
        return err("Wrong username or password.")
    login(request, user)
    return JsonResponse({"username": user.username})


@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    return JsonResponse({"ok": True})


@require_http_methods(["GET"])
def me_view(request):
    if not request.user.is_authenticated:
        return unauth()
    return JsonResponse({"username": request.user.username})


# ---------- generic CRUD ----------
def save(cfg, obj, data):
    created = obj is None
    obj = obj or cfg["model"]()
    for key in cfg["keys"]:
        value = data.get(key)
        if value is None or str(value).strip() == "":
            return err("Please fill in all the fields.")
        setattr(obj, key, value.strip() if isinstance(value, str) else value)
    try:
        obj.full_clean()
        obj.save()
    except ValidationError as e:
        return err(" ".join(e.messages))
    return JsonResponse(cfg["ser"](obj), status=201 if created else 200)


@require_http_methods(["GET", "POST"])
def collection(request, name):
    if not request.user.is_authenticated:
        return unauth()
    cfg = RESOURCES.get(name)
    if not cfg:
        return err("Unknown resource.", 404)
    if request.method == "GET":
        return JsonResponse([cfg["ser"](o) for o in cfg["model"].objects.all()], safe=False)
    return save(cfg, None, body(request))


@require_http_methods(["GET", "PUT", "DELETE"])
def item(request, name, pk):
    if not request.user.is_authenticated:
        return unauth()
    cfg = RESOURCES.get(name)
    if not cfg:
        return err("Unknown resource.", 404)
    obj = cfg["model"].objects.filter(pk=pk).first()
    if obj is None:
        return err("Not found.", 404)
    if request.method == "GET":
        return JsonResponse(cfg["ser"](obj))
    if request.method == "DELETE":
        obj.delete()
        return JsonResponse({"ok": True})
    return save(cfg, obj, body(request))


@require_http_methods(["POST"])
def election_status(request, pk):
    if not request.user.is_authenticated:
        return unauth()
    election = Election.objects.filter(pk=pk).first()
    if election is None:
        return err("Not found.", 404)
    status = body(request).get("status")
    if status not in ("Pending", "Ongoing", "Ended"):
        return err("Invalid status.")
    election.status = status
    election.save()
    return JsonResponse(ser_election(election))


# ---------- ballot ----------
@require_http_methods(["GET"])
def ballot_list(request):
    if not request.user.is_authenticated:
        return unauth()
    rows = [dict(id=b.pk, election_title=b.election.title, position_title=b.position.title,
                 candidate_name=b.candidate.student.name)
            for b in Ballot.objects.select_related("election", "position", "candidate__student")]
    return JsonResponse(rows, safe=False)


@require_http_methods(["GET"])
def ballot_form(request, election_id):
    if not request.user.is_authenticated:
        return unauth()
    election = Election.objects.filter(pk=election_id).first()
    if election is None:
        return err("Not found.", 404)
    positions = []
    for p in election.positions.all():
        cands = [dict(id=c.pk, name=c.student.name) for c in p.candidates.select_related("student")]
        if cands:
            positions.append(dict(id=p.pk, title=p.title, candidates=cands))
    voters = [dict(id=v.pk, label=f"V{v.pk} - {v.student.name}")
              for v in election.voters.filter(status="Not voted").select_related("student")]
    return JsonResponse(dict(status=election.status, positions=positions, voters=voters))


@require_http_methods(["POST"])
def ballot_submit(request):
    if not request.user.is_authenticated:
        return unauth()
    data = body(request)
    election = Election.objects.filter(pk=data.get("election") or 0).first()
    if election is None:
        return err("Please select an election.")
    if election.status != "Ongoing":
        return err("This election is not open for voting.")
    voter = Voter.objects.filter(pk=data.get("voter") or 0, election=election).first()
    if voter is None:
        return err("Please select a registered voter for this election.")
    choices = data.get("choices") or {}
    positions = [p for p in election.positions.all() if p.candidates.exists()]
    if not positions:
        return err("This election has no positions with candidates.")
    picked = []
    for p in positions:
        cand = p.candidates.filter(pk=choices.get(str(p.pk)) or 0).first()
        if cand is None:
            return err(f"Please choose a candidate for {p.title}.")
        picked.append((p, cand))
    with transaction.atomic():
        voter = Voter.objects.select_for_update().get(pk=voter.pk)
        if voter.status == "Voted":
            return err("This voter has already voted.")
        for p, cand in picked:
            Ballot.objects.create(election=election, position=p, candidate=cand)
            Candidate.objects.filter(pk=cand.pk).update(votes=F("votes") + 1)
        voter.status = "Voted"
        voter.save()
    return JsonResponse({"ok": True})
