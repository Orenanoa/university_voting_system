from django.contrib import admin

from .models import Ballot, Candidate, Election, Position, Student, Voter

admin.site.site_header = "Student Voting System"
admin.site.site_title = "Voting Admin"
admin.site.index_title = "Manage the election data"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "first_name", "last_name", "gender", "course", "year", "session")
    list_filter = ("gender", "year", "session")
    search_fields = ("student_id", "first_name", "last_name", "course")


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ("title", "status")
    list_filter = ("status",)
    search_fields = ("title",)
    actions = ["start", "end"]

    @admin.action(description="Start selected elections")
    def start(self, request, queryset):
        queryset.update(status="Ongoing")

    @admin.action(description="End selected elections")
    def end(self, request, queryset):
        queryset.update(status="Ended")


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("title", "election")
    list_filter = ("election",)
    search_fields = ("title", "description")


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("student", "position", "votes")
    list_filter = ("position__election", "position")
    search_fields = ("student__first_name", "student__last_name", "student__student_id")
    readonly_fields = ("votes",)


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "election", "age", "status")
    list_filter = ("election", "status")
    search_fields = ("student__first_name", "student__last_name", "student__student_id")


@admin.register(Ballot)
class BallotAdmin(admin.ModelAdmin):
    """Ballots are anonymous records: view only."""
    list_display = ("id", "election", "position", "candidate")
    list_filter = ("election", "position")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
