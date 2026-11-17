from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import RedirectView

from voting import views as v

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="home")),
    path("login/", auth_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("home/", v.HomeView.as_view(), name="home"),
    path("ballot/", v.BallotView.as_view(), name="ballot"),
    path("elections/<int:pk>/status/<str:status>/", v.ElectionStatus.as_view(), name="election-status"),
]

for res, (lst, upd, dele) in {
    "students": (v.StudentList, v.StudentUpdate, v.StudentDelete),
    "elections": (v.ElectionList, v.ElectionUpdate, v.ElectionDelete),
    "positions": (v.PositionList, v.PositionUpdate, v.PositionDelete),
    "candidates": (v.CandidateList, v.CandidateUpdate, v.CandidateDelete),
    "voters": (v.VoterList, v.VoterUpdate, v.VoterDelete),
}.items():
    urlpatterns += [
        path(f"{res}/", lst.as_view(), name=f"{res}-list"),
        path(f"{res}/<int:pk>/edit/", upd.as_view(), name=f"{res}-edit"),
        path(f"{res}/<int:pk>/delete/", dele.as_view(), name=f"{res}-delete"),
    ]
