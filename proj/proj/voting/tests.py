from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Ballot, Candidate, Election, Student, Voter


class VotingTests(TestCase):
    def setUp(self):
        call_command("ensure_admin", verbosity=0)
        call_command("seed_demo", verbosity=0)
        self.client.login(username="admin", password="admin123")

    # authentication
    def test_pages_need_login(self):
        self.client.logout()
        for name in ("home", "students-list", "elections-list", "ballot"):
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 302)
            self.assertIn("/login/", r["Location"])

    def test_login_logout(self):
        self.client.logout()
        bad = self.client.post(reverse("login"), {"username": "admin", "password": "x"})
        self.assertContains(bad, "Wrong username or password")
        ok = self.client.post(reverse("login"), {"username": "admin", "password": "admin123"})
        self.assertRedirects(ok, reverse("home"))
        self.client.post(reverse("logout"))
        self.assertEqual(self.client.get(reverse("home")).status_code, 302)

    # templates
    def test_templates_extend_base(self):
        r = self.client.get(reverse("students-list"))
        self.assertTemplateUsed(r, "base.html")
        self.assertTemplateUsed(r, "crud/list.html")

    # forms + CRUD
    def test_student_crud(self):
        data = dict(student_id="S100", first_name="Test", last_name="User", gender="Male",
                    course="Law", year="Year 2", session="Day")
        self.assertRedirects(self.client.post(reverse("students-list"), data), reverse("students-list"))
        s = Student.objects.get(student_id="S100")
        dup = self.client.post(reverse("students-list"), data)
        self.assertContains(dup, "already exists")
        data["course"] = "Education"
        self.client.post(reverse("students-edit", args=[s.pk]), data)
        s.refresh_from_db()
        self.assertEqual(s.course, "Education")
        self.assertEqual(self.client.get(reverse("students-delete", args=[s.pk])).status_code, 200)
        self.client.post(reverse("students-delete", args=[s.pk]))
        self.assertFalse(Student.objects.filter(pk=s.pk).exists())

    def test_invalid_form_rejected(self):
        r = self.client.post(reverse("students-list"), {"student_id": ""})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "This field is required")

    def test_election_position_candidate_voter_crud(self):
        self.client.post(reverse("elections-list"), {"title": "New Poll", "status": "Pending"})
        e = Election.objects.get(title="New Poll")
        self.client.post(reverse("positions-list"), {"election": e.pk, "title": "Chair", "description": "Leads"})
        p = e.positions.get()
        self.client.post(reverse("candidates-list"), {"student": 1, "position": p.pk})
        self.assertEqual(p.candidates.count(), 1)
        self.client.post(reverse("voters-list"), {"election": e.pk, "student": 2, "age": 20})
        dup = self.client.post(reverse("voters-list"), {"election": e.pk, "student": 2, "age": 20})
        self.assertContains(dup, "already exists")
        self.client.post(reverse("election-status", args=[e.pk, "Ongoing"]))
        e.refresh_from_db()
        self.assertEqual(e.status, "Ongoing")
        self.client.post(reverse("elections-delete", args=[e.pk]))
        self.assertFalse(Candidate.objects.filter(position__title="Chair").exists())

    def test_ballot_flow(self):
        r = self.client.get(reverse("ballot"), {"election": 1})
        form = r.context["form"]
        voter = form.fields["voter"].queryset.first()
        post = {"election": 1, "voter": voter.pk}
        for name in form.position_fields:
            post[name] = form.fields[name].queryset.first().pk
        self.assertEqual(self.client.post(reverse("ballot"), {"election": 1, "voter": voter.pk}).status_code, 200)
        self.assertEqual(Ballot.objects.count(), 0)
        self.assertEqual(self.client.post(reverse("ballot"), post).status_code, 302)
        self.assertEqual(Voter.objects.get(pk=voter.pk).status, "Voted")
        self.assertEqual(Ballot.objects.count(), len(form.position_fields))
        self.assertEqual(sum(c.votes for c in Candidate.objects.all()), len(form.position_fields))
        self.client.post(reverse("ballot"), post)  # second attempt rejected
        self.assertEqual(Ballot.objects.count(), len(form.position_fields))
        Election.objects.filter(pk=1).update(status="Ended")
        self.client.post(reverse("ballot"), post)
        self.assertEqual(Ballot.objects.count(), len(form.position_fields))

    # admin
    def test_admin_customised(self):
        self.assertContains(self.client.get("/admin/"), "Student Voting System Admin")
        self.assertContains(self.client.get("/admin/voting/student/"), "Year")  # list_filter
        self.assertEqual(self.client.get("/admin/voting/ballot/add/").status_code, 403)
