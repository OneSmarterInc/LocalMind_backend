from django.urls import path

from .views import (
    ConfirmOutlineView,
    DocumentChaptersView,
    DocumentDetailView,
    DocumentOutlineView,
    DocumentStructureView,
    DocumentUploadView,
    ProcessDocumentView,
)

urlpatterns = [
    path("upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("<uuid:document_id>/", DocumentDetailView.as_view(), name="document-detail"),
    path("<uuid:document_id>/process/", ProcessDocumentView.as_view(), name="document-process"),
    path("<uuid:document_id>/chapters/", DocumentChaptersView.as_view(), name="document-chapters"),
    path("<uuid:document_id>/structure/", DocumentStructureView.as_view(), name="document-structure"),
    path("<uuid:document_id>/outline/", DocumentOutlineView.as_view(), name="document-outline"),
    path(
        "<uuid:document_id>/outline/confirm/",
        ConfirmOutlineView.as_view(),
        name="document-outline-confirm",
    ),
]
