from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView, TemplateView
from django.views.static import serve

pages = ["login", "home", "students", "election", "position", "candidate", "voter", "ballot"]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url="/login.html")),
    path("logo.png", serve, {"document_root": settings.BASE_DIR / "voting" / "static", "path": "logo.png"}),
]

urlpatterns += [
    path(f"{p}.html", TemplateView.as_view(template_name=f"{p}.html"))
    for p in pages
]
