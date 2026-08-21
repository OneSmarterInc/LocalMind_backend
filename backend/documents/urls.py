from django.urls import path
from .views import (
    ConfirmOutlineView,
    DocumentDetailView,
    DocumentOutlineView,
    DocumentUploadView,
)

urlpatterns = [
    path("upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("<uuid:document_id>/", DocumentDetailView.as_view(), name="document-detail"),
    path("<uuid:document_id>/outline/", DocumentOutlineView.as_view(), name="document-outline"),
    path(
        "<uuid:document_id>/outline/confirm/",
        ConfirmOutlineView.as_view(),
        name="document-outline-confirm",
    ),
]
