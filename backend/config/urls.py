from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("api/documents/", include("documents.urls")),
    path("api/learning/", include("learning.urls")),
    path("api/tutor/", include("tutor.urls")),
]

