from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import RedirectView, TemplateView
from django.views.static import serve

from voting import api

pages = ["home", "students", "election", "position", "candidate", "voter", "ballot"]


def page(name, protected=True):
    view = ensure_csrf_cookie(TemplateView.as_view(template_name=f"{name}.html"))
    return login_required(view) if protected else view


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url="/login.html")),
    path("logo.png", serve, {"document_root": settings.BASE_DIR / "voting" / "static", "path": "logo.png"}),
    path("login.html", page("login", protected=False)),
    # JSON API
    path("api/login/", api.login_view),
    path("api/logout/", api.logout_view),
    path("api/me/", api.me_view),
    path("api/ballot/", api.ballot_list),
    path("api/ballot/submit/", api.ballot_submit),
    path("api/ballot/form/<int:election_id>/", api.ballot_form),
    path("api/election/<int:pk>/status/", api.election_status),
    path("api/<str:name>/", api.collection),
    path("api/<str:name>/<int:pk>/", api.item),
]
urlpatterns += [path(f"{p}.html", page(p)) for p in pages]
