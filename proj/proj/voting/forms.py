from django import forms
from django.db import transaction
from django.db.models import F

from .models import Ballot, Candidate, Election, Position, Student, Voter


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["student_id", "first_name", "last_name", "gender", "course", "year", "session"]
        labels = {"student_id": "Student ID", "year": "Year of Study"}


class ElectionForm(forms.ModelForm):
    class Meta:
        model = Election
        fields = ["title", "status"]
        widgets = {"title": forms.TextInput(attrs={"placeholder": "e.g. Guild Elections 2026"})}


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ["election", "title", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ["student", "position"]


class VoterForm(forms.ModelForm):
    class Meta:
        model = Voter
        fields = ["election", "student", "age"]

    def clean_age(self):
        age = self.cleaned_data["age"]
        if age < 16 or age > 100:
            raise forms.ValidationError("Enter a realistic age (16-100).")
        return age


class BallotForm(forms.Form):
    """Cast one ballot. A radio field per position is added for the chosen election."""

    voter = forms.ModelChoiceField(queryset=Voter.objects.none(), empty_label="-- Select voter --")

    def __init__(self, election, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.election = election
        self.fields["voter"].queryset = election.voters.filter(status="Not voted").select_related("student")
        self.fields["voter"].label_from_instance = lambda v: f"V{v.pk} - {v.student.name}"
        self.position_fields = []
        for p in election.positions.all():
            candidates = p.candidates.select_related("student")
            if not candidates:
                continue
            name = f"position_{p.pk}"
            field = forms.ModelChoiceField(queryset=candidates, widget=forms.RadioSelect,
                                           empty_label=None, label=p.title)
            field.label_from_instance = lambda c: c.student.name
            self.fields[name] = field
            self.position_fields.append(name)

    def clean(self):
        data = super().clean()
        if self.election.status != "Ongoing":
            raise forms.ValidationError("This election is not open for voting.")
        if not self.position_fields:
            raise forms.ValidationError("This election has no positions with candidates.")
        return data

    def save(self):
        voter_id = self.cleaned_data["voter"].pk
        with transaction.atomic():
            voter = Voter.objects.select_for_update().get(pk=voter_id)
            if voter.status == "Voted":
                raise forms.ValidationError("This voter has already voted.")
            for name in self.position_fields:
                cand = self.cleaned_data[name]
                Ballot.objects.create(election=self.election, position=cand.position, candidate=cand)
                Candidate.objects.filter(pk=cand.pk).update(votes=F("votes") + 1)
            voter.status = "Voted"
            voter.save()
