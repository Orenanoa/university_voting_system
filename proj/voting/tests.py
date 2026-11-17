import json

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from .models import Candidate, Voter


class VotingApiTests(TestCase):
    def setUp(self):
        call_command("ensure_admin", verbosity=0)
        call_command("seed_demo", verbosity=0)
        self.client.login(username="admin", password="admin123")

    def call(self, method, url, data=None):
        return getattr(self.client, method)(url, json.dumps(data or {}), content_type="application/json")

    def test_pages_need_login(self):
        self.client.logout()
        self.assertEqual(self.client.get("/students.html").status_code, 302)
        self.assertEqual(self.client.get("/api/student/").status_code, 401)

    def test_login_api(self):
        self.client.logout()
        self.assertEqual(self.call("post", "/api/login/", {"username": "admin", "password": "x"}).status_code, 400)
        self.assertEqual(self.call("post", "/api/login/", {"username": "admin", "password": "admin123"}).status_code, 200)

    def test_student_crud(self):
        data = dict(student_id="S100", first_name="Test", last_name="User", gender="Male",
                    course="Law", year="Year 2", session="Day")
        r = self.call("post", "/api/student/", data)
        self.assertEqual(r.status_code, 201)
        pk = r.json()["id"]
        self.assertEqual(self.call("post", "/api/student/", data).status_code, 400)  # duplicate ID
        data["course"] = "Education"
        self.assertEqual(self.call("put", f"/api/student/{pk}/", data).json()["course"], "Education")
        self.assertEqual(self.client.get(f"/api/student/{pk}/").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/student/{pk}/").status_code, 200)
        self.assertEqual(self.client.get(f"/api/student/{pk}/").status_code, 404)

    def test_election_position_candidate_voter_crud(self):
        e = self.call("post", "/api/election/", {"title": "New Poll", "status": "Pending"}).json()
        self.assertEqual(e["voters"], 0)
        p = self.call("post", "/api/position/", {"election_id": e["id"], "title": "Chair", "description": "Leads"})
        self.assertEqual(p.status_code, 201)
        c = self.call("post", "/api/candidate/", {"student_id": 1, "position_id": p.json()["id"]})
        self.assertEqual(c.status_code, 201)
        v = self.call("post", "/api/voter/", {"election_id": e["id"], "student_id": 2, "age": 20})
        self.assertEqual(v.status_code, 201)
        self.assertEqual(self.call("post", "/api/voter/", {"election_id": e["id"], "student_id": 2, "age": 20}).status_code, 400)
        self.assertEqual(self.call("post", f"/api/election/{e['id']}/status/", {"status": "Ongoing"}).json()["status"], "Ongoing")
        self.assertEqual(self.client.delete(f"/api/election/{e['id']}/").status_code, 200)
        self.assertFalse(Candidate.objects.filter(position__title="Chair").exists())

    def test_full_ballot_flow(self):
        form = self.client.get("/api/ballot/form/1/").json()
        voter = form["voters"][0]["id"]
        choices = {str(p["id"]): p["candidates"][0]["id"] for p in form["positions"]}
        self.assertEqual(self.call("post", "/api/ballot/submit/", {"election": 1, "voter": voter, "choices": {}}).status_code, 400)
        self.assertEqual(self.call("post", "/api/ballot/submit/", {"election": 1, "voter": voter, "choices": choices}).status_code, 200)
        self.assertEqual(Voter.objects.get(pk=voter).status, "Voted")
        self.assertEqual(sum(c.votes for c in Candidate.objects.all()), len(choices))
        # one ballot per voter
        self.assertEqual(self.call("post", "/api/ballot/submit/", {"election": 1, "voter": voter, "choices": choices}).status_code, 400)
        # closed election
        self.call("post", "/api/election/1/status/", {"status": "Ended"})
        other = Voter.objects.filter(status="Not voted").first().pk
        self.assertEqual(self.call("post", "/api/ballot/submit/", {"election": 1, "voter": other, "choices": choices}).status_code, 400)
        self.assertEqual(len(self.client.get("/api/ballot/").json()), len(choices))
