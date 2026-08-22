import uuid
import documents.models
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(blank=True, max_length=300)),
                ("original_name", models.CharField(max_length=300)),
                ("file", models.FileField(upload_to=documents.models.document_upload_path)),
                ("file_type", models.CharField(max_length=10)),
                ("status", models.CharField(
                    choices=[
                        ("uploaded", "Uploaded"),
                        ("processing", "Processing"),
                        ("awaiting_review", "Awaiting review"),
                        ("confirmed", "Confirmed"),
                        ("error", "Error"),
                    ],
                    default="uploaded",
                    max_length=30,
                )),
                ("processed_markdown_path", models.CharField(blank=True, max_length=500)),
                ("extracted_headings", models.JSONField(blank=True, default=list)),
                ("outline_source", models.CharField(blank=True, max_length=30)),
                ("error_message", models.TextField(blank=True)),
                ("outline_confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
