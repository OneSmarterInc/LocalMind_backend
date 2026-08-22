from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from documents.models import Document
from documents.services.outline import build_proposed_outline
from documents.services.parser import extract_sections_from_markdown
from learning.models import Chapter, LearningModule


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
        self.assertEqual(response.json()["chapters"], [])

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


class SourceHierarchyTests(TestCase):
    def test_source_hierarchy_does_not_invent_overview_module(self):
        document = Document(
            original_name="book.pdf",
            title="book",
            file_type="pdf",
        )
        sections = [
            {
                "index": 0,
                "level": 1,
                "title": "Introduction",
                "source_text": "Complete introduction text",
                "start_page": 1,
                "end_page": 2,
            },
            {
                "index": 1,
                "level": 1,
                "title": "Conclusion",
                "source_text": "Complete conclusion text",
                "start_page": 3,
                "end_page": 3,
            },
        ]

        outline, source = build_proposed_outline(document, sections)

        self.assertEqual(source, "source_hierarchy")
        self.assertEqual(outline["chapters"][0]["title"], "Introduction")
        self.assertEqual(outline["chapters"][0]["modules"], [])

    def test_single_h1_remains_the_chapter_and_h2_becomes_modules(self):
        document = Document(
            original_name="Chapter_02_Personal_Cybersecurity.docx",
            title="Chapter_02_Personal_Cybersecurity",
            file_type="docx",
        )
        sections = [
            {
                "index": 0,
                "level": 1,
                "title": "Chapter 2: Personal Cybersecurity",
                "source_text": "Complete chapter content",
                "start_page": None,
                "end_page": None,
            },
            {
                "index": 1,
                "level": 2,
                "title": "Chapter Objectives",
                "source_text": "Objectives",
                "start_page": None,
                "end_page": None,
            },
            {
                "index": 2,
                "level": 2,
                "title": "Section 1: Protecting Personal Data",
                "source_text": "Section content with nested heading",
                "start_page": None,
                "end_page": None,
            },
            {
                "index": 3,
                "level": 3,
                "title": "Creating Strong, Unique Passwords",
                "source_text": "Password content",
                "start_page": None,
                "end_page": None,
            },
        ]

        outline, source = build_proposed_outline(document, sections)

        self.assertEqual(source, "source_hierarchy")
        self.assertEqual(len(outline["chapters"]), 1)
        self.assertEqual(
            outline["chapters"][0]["title"],
            "Chapter 2: Personal Cybersecurity",
        )
        self.assertEqual(
            [m["title"] for m in outline["chapters"][0]["modules"]],
            ["Chapter Objectives", "Section 1: Protecting Personal Data"],
        )
        self.assertEqual(
            outline["document_title"],
            "Chapter 2: Personal Cybersecurity",
        )

    def test_inline_markdown_heading_is_recovered(self):
        markdown = (
            "# Chapter 2: Personal Cybersecurity\n"
            "## Chapter Objectives\n"
            "Objective text. ## Introduction to Personal Cybersecurity\n"
            "Introduction body.\n"
            "## Introducing Sam\n"
            "Sam body."
        )

        sections = extract_sections_from_markdown(markdown)
        titles = [(s["level"], s["title"]) for s in sections]

        self.assertEqual(
            titles,
            [
                (1, "Chapter 2: Personal Cybersecurity"),
                (2, "Chapter Objectives"),
                (2, "Introduction to Personal Cybersecurity"),
                (2, "Introducing Sam"),
            ],
        )
        objectives = sections[1]
        self.assertEqual(objectives["source_text"], "Objective text.")


class DocumentProcessingApiTests(TestCase):
    def setUp(self):
        uploaded_file = SimpleUploadedFile(
            "computer_networks.pdf",
            b"%PDF-1.4 test content",
            content_type="application/pdf",
        )
        self.document = Document.objects.create(
            title="Computer Networks",
            original_name="computer_networks.pdf",
            file=uploaded_file,
            file_type="pdf",
        )

    @patch("documents.views.parse_document")
    def test_process_document_persists_actual_chapter_and_module_text(
        self,
        mock_parse_document,
    ):
        sections = [
            {
                "index": 0,
                "level": 1,
                "title": "Computer Networks",
                "source_text": (
                    "This is the complete chapter introduction.\n\n"
                    "## OSI Model\nOSI has seven layers."
                ),
                "start_page": 1,
                "end_page": 5,
            },
            {
                "index": 1,
                "level": 2,
                "title": "OSI Model",
                "source_text": "OSI has seven layers.",
                "start_page": 2,
                "end_page": 3,
            },
        ]

        mock_parse_document.return_value = {
            "markdown": "# Computer Networks\n## OSI Model",
            "markdown_path": "/tmp/document.md",
            "headings": [
                {
                    "index": 0,
                    "level": 1,
                    "title": "Computer Networks",
                    "start_page": 1,
                    "end_page": 5,
                },
                {
                    "index": 1,
                    "level": 2,
                    "title": "OSI Model",
                    "start_page": 2,
                    "end_page": 3,
                },
            ],
            "sections": sections,
            "parse_mode": "fast_no_ocr",
        }

        response = self.client.post(
            reverse("document-process", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Chapter.objects.count(), 1)
        self.assertEqual(LearningModule.objects.count(), 1)

        chapter = Chapter.objects.get()
        module = LearningModule.objects.get()

        self.assertEqual(chapter.document, self.document)
        self.assertEqual(
            chapter.source_text,
            "This is the complete chapter introduction.\n\n"
            "## OSI Model\nOSI has seven layers.",
        )
        self.assertEqual(chapter.start_page, 1)
        self.assertEqual(chapter.end_page, 5)

        self.assertEqual(module.chapter, chapter)
        self.assertEqual(module.title, "OSI Model")
        self.assertEqual(module.source_text, "OSI has seven layers.")
        self.assertEqual(module.start_page, 2)
        self.assertEqual(module.end_page, 3)

        payload = response.json()
        self.assertEqual(payload["outline_source"], "source_hierarchy")
        self.assertNotIn("modules", payload)
        self.assertEqual(len(payload["chapters"]), 1)
        self.assertEqual(len(payload["chapters"][0]["modules"]), 1)
        self.assertEqual(
            payload["chapters"][0]["modules"][0]["source_text"],
            "OSI has seven layers.",
        )

    @patch("documents.views.parse_document")
    def test_chapter_without_source_subheading_has_empty_modules(
        self,
        mock_parse_document,
    ):
        sections = [
            {
                "index": 0,
                "level": 1,
                "title": "Introduction",
                "source_text": "Actual introduction text.",
                "start_page": 1,
                "end_page": 2,
            },
            {
                "index": 1,
                "level": 1,
                "title": "Conclusion",
                "source_text": "Actual conclusion text.",
                "start_page": 3,
                "end_page": 3,
            },
        ]

        mock_parse_document.return_value = {
            "markdown": "# Introduction\n# Conclusion",
            "markdown_path": "/tmp/document.md",
            "headings": [
                {
                    "index": item["index"],
                    "level": item["level"],
                    "title": item["title"],
                    "start_page": item["start_page"],
                    "end_page": item["end_page"],
                }
                for item in sections
            ],
            "sections": sections,
            "parse_mode": "fast_no_ocr",
        }

        response = self.client.post(
            reverse("document-process", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Chapter.objects.count(), 2)
        self.assertEqual(LearningModule.objects.count(), 0)
        self.assertEqual(response.json()["chapters"][0]["modules"], [])

    @patch("documents.views.parse_document")
    def test_processing_failure_sets_error_status(self, mock_parse_document):
        mock_parse_document.side_effect = ValueError("Unreadable PDF")

        response = self.client.post(
            reverse("document-process", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 422)
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, Document.Status.ERROR)
        self.assertIn("Unreadable PDF", self.document.error_message)

    @patch("documents.views.parse_document")
    def test_real_chapter_api_returns_persisted_sqlite_content(
        self,
        mock_parse_document,
    ):
        sections = [
            {
                "index": 0,
                "level": 1,
                "title": "Introduction",
                "source_text": "Actual persisted chapter text.",
                "start_page": 1,
                "end_page": 2,
            }
        ]
        mock_parse_document.return_value = {
            "markdown": "# Introduction",
            "markdown_path": "/tmp/document.md",
            "headings": [
                {
                    "index": 0,
                    "level": 1,
                    "title": "Introduction",
                    "start_page": 1,
                    "end_page": 2,
                }
            ],
            "sections": sections,
            "parse_mode": "fast_no_ocr",
        }

        process_response = self.client.post(
            reverse("document-process", args=[self.document.id])
        )
        self.assertEqual(process_response.status_code, 200)

        response = self.client.get(
            reverse("document-chapters", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["document_id"], str(self.document.id))
        self.assertEqual(
            payload["chapters"][0]["source_text"],
            "Actual persisted chapter text.",
        )


class DocumentStructureApiTests(TestCase):
    def setUp(self):
        uploaded_file = SimpleUploadedFile(
            "cybersecurity.docx",
            b"test content",
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        )
        self.document = Document.objects.create(
            title="Personal Cybersecurity",
            original_name="cybersecurity.docx",
            file=uploaded_file,
            file_type="docx",
            status=Document.Status.AWAITING_REVIEW,
        )

        self.chapter_one = Chapter.objects.create(
            document=self.document,
            title="Protecting Personal Data",
            order=1,
            source_text="Large chapter source text that should not be returned.",
        )
        self.chapter_two = Chapter.objects.create(
            document=self.document,
            title="Safe Internet Practices",
            order=2,
            source_text="Another large chapter source text.",
        )

        LearningModule.objects.create(
            chapter=self.chapter_one,
            title="Creating Strong, Unique Passwords",
            order=1,
            source_text="Large module source text that should not be returned.",
        )
        LearningModule.objects.create(
            chapter=self.chapter_one,
            title="Using Password Managers",
            order=2,
            source_text="Another module source text.",
        )

    def test_structure_api_returns_chapter_and_module_names_only(self):
        response = self.client.get(
            reverse("document-structure", args=[self.document.id])
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["document_id"], str(self.document.id))
        self.assertEqual(payload["title"], "Personal Cybersecurity")
        self.assertEqual(payload["status"], Document.Status.AWAITING_REVIEW)
        self.assertEqual(len(payload["chapters"]), 2)

        first_chapter = payload["chapters"][0]
        self.assertEqual(first_chapter["title"], "Protecting Personal Data")
        self.assertEqual(first_chapter["order"], 1)
        self.assertNotIn("source_text", first_chapter)
        self.assertEqual(len(first_chapter["modules"]), 2)

        first_module = first_chapter["modules"][0]
        self.assertEqual(
            first_module["title"],
            "Creating Strong, Unique Passwords",
        )
        self.assertEqual(first_module["order"], 1)
        self.assertNotIn("source_text", first_module)

        second_chapter = payload["chapters"][1]
        self.assertEqual(second_chapter["title"], "Safe Internet Practices")
        self.assertEqual(second_chapter["modules"], [])