from django.db import models


class Student(models.Model):
    GENDERS = [("Male", "Male"), ("Female", "Female")]
    YEARS = [(f"Year {i}", f"Year {i}") for i in range(1, 5)]
    SESSIONS = [("Day", "Day"), ("Evening", "Evening"), ("Weekend", "Weekend")]

    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    gender = models.CharField(max_length=10, choices=GENDERS)
    course = models.CharField(max_length=120)
    year = models.CharField(max_length=10, choices=YEARS)
    session = models.CharField(max_length=10, choices=SESSIONS)

    class Meta:
        ordering = ["student_id"]

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.student_id} - {self.name}"


class Election(models.Model):
    STATUSES = [("Pending", "Pending"), ("Ongoing", "Ongoing"), ("Ended", "Ended")]

    title = models.CharField(max_length=150, unique=True)
    status = models.CharField(max_length=10, choices=STATUSES, default="Pending")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.title


class Position(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="positions")
    title = models.CharField(max_length=120)
    description = models.TextField()

    class Meta:
        ordering = ["id"]
        unique_together = [("election", "title")]

    def __str__(self):
        return f"{self.title} ({self.election})"


class Candidate(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="candidacies")
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name="candidates")
    votes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position_id", "id"]
        unique_together = [("student", "position")]

    def __str__(self):
        return f"{self.student.name} for {self.position.title}"


class Voter(models.Model):
    STATUSES = [("Not voted", "Not voted"), ("Voted", "Voted")]

    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="voters")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="voter_records")
    age = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUSES, default="Not voted")

    class Meta:
        ordering = ["id"]
        unique_together = [("election", "student")]

    def __str__(self):
        return f"{self.student.name} @ {self.election}"


class Ballot(models.Model):
    """One anonymous choice. Deliberately not linked to a Voter."""
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="ballots")
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)

    class Meta:
        ordering = ["id"]
