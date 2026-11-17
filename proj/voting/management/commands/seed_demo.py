from django.core.management.base import BaseCommand

from voting.models import Candidate, Election, Position, Student, Voter


class Command(BaseCommand):
    help = "Load sample data (only if there are no students yet)"

    def handle(self, *args, **options):
        if Student.objects.exists():
            self.stdout.write("Data already present - skipped.")
            return
        rows = [("S001", "Aisha", "Nakato", "Female", "Computer Science", "Year 3", "Day"),
                ("S002", "Ibrahim", "Mugisha", "Male", "Business Administration", "Year 2", "Evening"),
                ("S003", "Maryam", "Namukasa", "Female", "Education", "Year 4", "Day"),
                ("S004", "Yusuf", "Kiggundu", "Male", "Law", "Year 1", "Weekend"),
                ("S005", "Halima", "Nabirye", "Female", "Information Technology", "Year 3", "Day")]
        s = {r[0]: Student.objects.create(student_id=r[0], first_name=r[1], last_name=r[2], gender=r[3],
                                          course=r[4], year=r[5], session=r[6]) for r in rows}
        guild = Election.objects.create(title="Guild Elections 2026", status="Ongoing")
        Election.objects.create(title="Faculty Representatives 2026", status="Pending")
        hall = Election.objects.create(title="Hall Council 2025", status="Ended")
        Election.objects.create(title="Freshers' Representatives 2026", status="Pending")
        Election.objects.create(title="Sports Council 2025", status="Ended")
        pos = {}
        for t, d in [("Guild President", "Leads the student guild and represents students to management."),
                     ("Vice President", "Deputises the President and coordinates guild committees."),
                     ("General Secretary", "Keeps guild records and minutes of meetings."),
                     ("Finance Secretary", "Manages the guild budget and accounts.")]:
            pos[t] = Position.objects.create(election=guild, title=t, description=d)
        Position.objects.create(election=hall, title="Hall Chairperson",
                                description="Leads the hall council and handles residents' concerns.")
        for sid, p in [("S001", "Guild President"), ("S004", "Guild President"), ("S003", "General Secretary"),
                       ("S002", "General Secretary"), ("S005", "Finance Secretary")]:
            Candidate.objects.create(student=s[sid], position=pos[p])
        for sid, age in [("S001", 21), ("S002", 20), ("S003", 23), ("S004", 19), ("S005", 22)]:
            Voter.objects.create(election=guild, student=s[sid], age=age)
        self.stdout.write(self.style.SUCCESS("Sample data loaded."))
