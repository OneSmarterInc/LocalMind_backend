from pathlib import Path
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer
from .services.parser import parse_document
from .services.outline import build_proposed_outline, replace_outline

class DocumentUploadView(APIView):

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
        document = Document.objects.get(pk=document_id)
        return Response(DocumentSerializer(document).data)

class DocumentOutlineView(APIView):
    def get(self, request, document_id):
        document = Document.objects.get(pk=document_id)
        return Response(DocumentSerializer(document).data)

    def put(self, request, document_id):
        document = Document.objects.get(pk=document_id)

        if document.status == Document.Status.CONFIRMED:
            return Response(
                {"detail": "This outline is already confirmed."},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            replace_outline(document, request.data, user_edited=True)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document.status = Document.Status.AWAITING_REVIEW
        document.outline_source = "student_edited"
        document.save(update_fields=["status", "outline_source", "updated_at"])

        return Response(DocumentSerializer(document).data)

class ConfirmOutlineView(APIView):
    def post(self, request, document_id):
        document = Document.objects.get(pk=document_id)

        if not document.modules.exists():
            return Response(
                {"detail": "Cannot confirm an empty outline."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document.status = Document.Status.CONFIRMED
        document.outline_confirmed_at = timezone.now()
        document.save(
            update_fields=["status", "outline_confirmed_at", "updated_at"]
        )

        return Response(DocumentSerializer(document).data)
