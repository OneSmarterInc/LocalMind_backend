import logging
import re
from pathlib import Path

from django.conf import settings
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

logger = logging.getLogger(__name__)

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
MIN_MEANINGFUL_TEXT_CHARS = 200


def _extract_headings(markdown: str):
    headings = []

    for line in markdown.splitlines():
        match = HEADING_RE.match(line.strip())
        if not match:
            continue

        title = match.group(2).strip()
        if not title:
            continue

        headings.append({
            "level": len(match.group(1)),
            "title": title,
        })

    return headings


def _has_meaningful_text(markdown: str) -> bool:
    """
    Decide whether the PDF already contains enough selectable/extractable text.

    We count letters and numbers rather than Markdown formatting characters.
    """
    meaningful_chars = sum(char.isalnum() for char in markdown)
    return meaningful_chars >= MIN_MEANINGFUL_TEXT_CHARS


def _convert_pdf(source: Path, use_ocr: bool):
    """
    Convert PDF using Docling.

    First pass:
      - OCR OFF
      - table structure OFF

    Fallback pass for scanned PDFs:
      - OCR ON
      - table structure OFF

    Table extraction is intentionally disabled because LocalMind Phase 1 only
    needs the document's learning structure/headings.
    """
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = use_ocr
    pipeline_options.do_table_structure = False

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options
            )
        }
    )

    result = converter.convert(source)
    return result.document.export_to_markdown()


def _convert_non_pdf(source: Path):
    """
    DOCX and other supported non-PDF formats do not need PDF OCR handling.
    """
    converter = DocumentConverter()
    result = converter.convert(source)
    return result.document.export_to_markdown()


def parse_document(document):
    source = Path(document.file.path)
    extension = source.suffix.lower()

    if extension == ".pdf":
        logger.info(
            "LocalMind: trying fast PDF extraction without OCR for %s",
            document.original_name,
        )

        markdown = _convert_pdf(source, use_ocr=False)

        if _has_meaningful_text(markdown):
            parse_mode = "fast_no_ocr"
            logger.info(
                "LocalMind: selectable text found; OCR skipped for %s",
                document.original_name,
            )
        else:
            logger.info(
                "LocalMind: insufficient text found; retrying with OCR for %s",
                document.original_name,
            )

            markdown = _convert_pdf(source, use_ocr=True)
            parse_mode = "ocr_fallback"

    else:
        logger.info(
            "LocalMind: processing non-PDF document %s",
            document.original_name,
        )
        markdown = _convert_non_pdf(source)
        parse_mode = "standard"

    if not markdown.strip():
        raise ValueError(
            "No readable content could be extracted from this document."
        )

    processed_dir = (
        Path(settings.MEDIA_ROOT)
        / "processed"
        / str(document.id)
    )
    processed_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = processed_dir / "document.md"
    markdown_path.write_text(markdown, encoding="utf-8")

    headings = _extract_headings(markdown)

    logger.info(
        "LocalMind: document processing complete. mode=%s headings=%s",
        parse_mode,
        len(headings),
    )

    return {
        "markdown": markdown,
        "markdown_path": str(markdown_path),
        "headings": headings,
        "parse_mode": parse_mode,
    }
