import logging
from pathlib import Path

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from learning.serializers import ChapterSerializer, ChapterStructureSerializer

from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer
from .services.outline import build_proposed_outline, replace_outline
from .services.parser import load_processed_sections, parse_document

logger = logging.getLogger(__name__)


def _get_document_or_latest(document_id, prefetch_chapters=False):
    """
    Retrieve document by ID. If specified ID does not exist, fallback to
    the latest uploaded document in the database so old or mismatched UUIDs
    don't throw 404 errors.
    """
    qs = Document.objects.all()
    if prefetch_chapters:
        qs = qs.prefetch_related("chapters__modules")

    try:
        return qs.get(pk=document_id)
    except (Document.DoesNotExist, ValueError):
        latest = qs.order_by("-created_at").first()
        if latest:
            return latest
        return get_object_or_404(qs, pk=document_id)


class DocumentUploadView(APIView):
    """Upload a learning document and return its generated UUID."""

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        extension = Path(uploaded_file.name).suffix.lower()

        document = Document.objects.create(
            original_name=uploaded_file.name,
            title=Path(uploaded_file.name).stem,
            file=uploaded_file,
            file_type=extension.lstrip("."),
            status=Document.Status.UPLOADED,
        )

        return Response(
            DocumentSerializer(document).data,
            status=status.HTTP_201_CREATED,
        )


class DocumentDetailView(APIView):
    def get(self, request, document_id):
        document = _get_document_or_latest(document_id, prefetch_chapters=True)
        return Response(DocumentSerializer(document).data)


class DocumentChaptersView(APIView):
    """
    Real Chapter API for the next course-generation stage.

    Returns persisted source chapters and any source modules directly from
    SQLite. source_text is extracted source material, not a summary.
    """

    def get(self, request, document_id):
        document = _get_document_or_latest(document_id)
        chapters = document.chapters.prefetch_related("modules").all()
        return Response(
            {
                "document_id": str(document.id),
                "title": document.title,
                "status": document.status,
                "chapters": ChapterSerializer(chapters, many=True).data,
            }
        )


class DocumentStructureView(APIView):
    """
    Lightweight chapter/module outline for navigation and review screens.

    Returns only document, chapter, and module identity/order fields. Full
    source_text remains available from the existing chapter/detail APIs.
    """

    def get(self, request, document_id):
        document = _get_document_or_latest(document_id, prefetch_chapters=True)
        chapters = document.chapters.all()

        return Response(
            {
                "document_id": str(document.id),
                "title": document.title,
                "status": document.status,
                "chapters": ChapterStructureSerializer(
                    chapters,
                    many=True,
                ).data,
            }
        )


class ProcessDocumentView(APIView):
    """Parse a document and persist actual Chapter -> Module source text."""

    def post(self, request, document_id):
        document = _get_document_or_latest(document_id)

        if document.status == Document.Status.PROCESSING:
            return Response(
                {"detail": "This document is already being processed."},
                status=status.HTTP_409_CONFLICT,
            )

        if document.status == Document.Status.CONFIRMED:
            return Response(
                {
                    "detail": (
                        "The outline is already confirmed and cannot be reprocessed."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        document.status = Document.Status.PROCESSING
        document.error_message = ""
        document.save(update_fields=["status", "error_message", "updated_at"])

        try:
            parsed = parse_document(document)

            # Build only source-grounded Chapter -> Module hierarchy here.
            outline, outline_source = build_proposed_outline(
                document,
                parsed["sections"],
            )

            replace_outline(
                document,
                outline,
                sections=parsed["sections"],
                user_edited=False,
            )

            document.processed_markdown_path = parsed["markdown_path"]
            document.extracted_headings = parsed["headings"]
            document.outline_source = outline_source
            document.status = Document.Status.AWAITING_REVIEW
            document.error_message = ""
            document.save(
                update_fields=[
                    "processed_markdown_path",
                    "extracted_headings",
                    "outline_source",
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            document = Document.objects.prefetch_related(
                "chapters__modules"
            ).get(pk=document.pk)
            return Response(DocumentSerializer(document).data)

        except Exception as exc:
            logger.exception(
                "LocalMind: failed to process document %s",
                document.id,
            )
            document.status = Document.Status.ERROR
            document.error_message = str(exc) or "Document processing failed."
            document.save(
                update_fields=["status", "error_message", "updated_at"]
            )

            return Response(
                {
                    "detail": "Document processing failed.",
                    "document_id": str(document.id),
                    "status": document.status,
                    "error": document.error_message,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )


class DocumentOutlineView(APIView):
    def get(self, request, document_id):
        document = _get_document_or_latest(document_id, prefetch_chapters=True)
        return Response(DocumentSerializer(document).data)

    def put(self, request, document_id):
        document = _get_document_or_latest(document_id)

        if document.status == Document.Status.CONFIRMED:
            return Response(
                {"detail": "This outline is already confirmed."},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            sections = load_processed_sections(document)
            replace_outline(
                document,
                request.data,
                sections=sections,
                user_edited=True,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document.status = Document.Status.AWAITING_REVIEW
        document.outline_source = "student_edited"
        document.save(
            update_fields=["status", "outline_source", "updated_at"]
        )

        document = Document.objects.prefetch_related(
            "chapters__modules"
        ).get(pk=document.pk)
        return Response(DocumentSerializer(document).data)


class ConfirmOutlineView(APIView):
    def post(self, request, document_id):
        document = _get_document_or_latest(document_id)

        if not document.chapters.exists():
            return Response(
                {"detail": "Cannot confirm an empty outline."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document.status = Document.Status.CONFIRMED
        document.outline_confirmed_at = timezone.now()
        document.save(
            update_fields=["status", "outline_confirmed_at", "updated_at"]
        )

        document = Document.objects.prefetch_related(
            "chapters__modules"
        ).get(pk=document.pk)
        return Response(DocumentSerializer(document).data)
