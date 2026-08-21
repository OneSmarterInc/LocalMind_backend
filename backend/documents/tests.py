from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from documents.models import Document


class DocumentUploadApiTests(TestCase):

    def test_upload_pdf(self):
        uploaded_file = SimpleUploadedFile(
            "test_book.pdf",
            b"%PDF-1.4 test content",
            content_type="application/pdf",
        )

        response = self.client.post(
            reverse("document-upload"),
            {"file": uploaded_file},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "uploaded")
        self.assertEqual(response.json()["original_name"], "test_book.pdf")
        self.assertEqual(response.json()["file_type"], "pdf")

        self.assertEqual(Document.objects.count(), 1)

    def test_reject_invalid_file_type(self):
        uploaded_file = SimpleUploadedFile(
            "test.txt",
            b"hello",
            content_type="text/plain",
        )

        response = self.client.post(
            reverse("document-upload"),
            {"file": uploaded_file},
        )

        self.assertEqual(response.status_code, 400)