import uuid
from pathlib import Path
from django.db import models

def document_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"documents/{instance.id}/original{suffix}"

class Document(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        AWAITING_REVIEW = "awaiting_review", "Awaiting review"
        CONFIRMED = "confirmed", "Confirmed"
        ERROR = "error", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300, blank=True)
    original_name = models.CharField(max_length=300)
    file = models.FileField(upload_to=document_upload_path)
    file_type = models.CharField(max_length=10)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.UPLOADED,
    )
    processed_markdown_path = models.CharField(max_length=500, blank=True)
    extracted_headings = models.JSONField(default=list, blank=True)
    outline_source = models.CharField(max_length=30, blank=True)
    error_message = models.TextField(blank=True)
    outline_confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or self.original_name
