from pathlib import Path
from django.conf import settings
from rest_framework import serializers
from .models import Document
from learning.serializers import LearningModuleSerializer

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}

class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["file"]

    def validate_file(self, value):
        extension = Path(value.name).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                "Supported files are PDF (.pdf), Word (.docx), and legacy Word (.doc)."
            )

        max_bytes = settings.LOCALMIND_MAX_UPLOAD_MB * 1024 * 1024
        if value.size > max_bytes:
            raise serializers.ValidationError(
                f"File is larger than {settings.LOCALMIND_MAX_UPLOAD_MB} MB."
            )

        if value.size == 0:
            raise serializers.ValidationError("The uploaded file is empty.")

        return value

class DocumentSerializer(serializers.ModelSerializer):
    modules = LearningModuleSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "original_name",
            "file_type",
            "status",
            "outline_source",
            "error_message",
            "created_at",
            "updated_at",
            "outline_confirmed_at",
            "modules",
        ]
