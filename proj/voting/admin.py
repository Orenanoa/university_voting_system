from django.contrib import admin

from .models import Ballot, Candidate, Election, Position, Student, Voter

for m in (Student, Election, Position, Candidate, Voter, Ballot):
    admin.site.register(m)
