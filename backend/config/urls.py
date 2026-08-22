from django.contrib import admin
from django.urls import include, path
from learning.views import ChapterListView, ChapterDetailView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("api/documents/", include("documents.urls")),
    path("api/learning/", include("learning.urls")),
    path("api/tutor/", include("tutor.urls")),
    # Direct Aliases so that /api/chapters/ and /api/chapters/<id>/ never return 404
    path("api/chapters/", ChapterListView.as_view(), name="api-chapters-alias"),
    path("api/chapters/<uuid:chapter_id>/", ChapterDetailView.as_view(), name="api-chapter-detail-alias"),
]
