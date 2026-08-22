import html
from pathlib import Path

from django.db import transaction

from learning.models import Chapter, LearningModule, MicroModule


def _clean_title(value):
    value = html.unescape(str(value or ""))
    return " ".join(value.split()).strip()


def _section_lookup(sections):
    return {section["index"]: section for section in sections}


def _choose_chapter_level(sections):
    """
    Respect the source document hierarchy exactly.

    The shallowest heading level is the chapter level. We intentionally do NOT
    demote a single H1 to H2. In Word, Heading 1 is the author's explicit
    highest-level outline choice.
    """
    levels = [section["level"] for section in sections if section.get("level")]
    return min(levels) if levels else None


def _source_hierarchy_outline(original_name, sections):
    """
    Build Document -> Chapter -> Module directly from the source hierarchy.

    Rules:
      * shallowest source heading level -> Chapter
      * immediate next available heading level inside that chapter -> Module
      * deeper headings stay inside Module.source_text as subheadings/content
    """
    default_title = Path(original_name).stem

    if not sections:
        raise ValueError("No source sections are available to persist.")

    chapter_level = _choose_chapter_level(sections)
    chapter_sections = [
        section
        for section in sections
        if section["level"] == chapter_level
    ]

    if not chapter_sections:
        chapter_sections = [sections[0]]
        chapter_level = sections[0]["level"]

    chapters = []

    for position, chapter_section in enumerate(chapter_sections):
        next_chapter_index = (
            chapter_sections[position + 1]["index"]
            if position + 1 < len(chapter_sections)
            else float("inf")
        )

        nested = [
            section
            for section in sections
            if chapter_section["index"] < section["index"] < next_chapter_index
            and section["level"] > chapter_level
        ]

        modules = []
        if nested:
            module_level = min(section["level"] for section in nested)
            modules = [
                {
                    "title": _clean_title(section["title"]),
                    "source_heading_index": section["index"],
                }
                for section in nested
                if section["level"] == module_level
            ]

        chapters.append(
            {
                "title": _clean_title(chapter_section["title"]),
                "source_heading_index": chapter_section["index"],
                "modules": modules,
            }
        )

    document_title = (
        chapters[0]["title"] if len(chapters) == 1 else default_title
    )

    return {
        "document_title": document_title,
        "chapters": chapters,
    }


def build_proposed_outline(document, sections):
    return (
        _source_hierarchy_outline(document.original_name, sections),
        "source_hierarchy",
    )


@transaction.atomic
def replace_outline(document, outline, sections=None, user_edited=False):
    """
    Persist Chapter -> Module/MicroModule rows in SQLite.

    source_text always comes from parsed source sections when a
    source_heading_index exists. It is never replaced with a summary.
    """
    chapters = outline.get("chapters") or []
    if not chapters:
        raise ValueError("The outline must contain at least one chapter.")

    sections = sections or []
    lookup = _section_lookup(sections)

    Chapter.objects.filter(document=document).delete()

    for chapter_order, chapter_data in enumerate(chapters, start=1):
        chapter_title = _clean_title(chapter_data.get("title"))
        modules = chapter_data.get("modules") or []

        if not chapter_title:
            raise ValueError(f"Chapter {chapter_order} needs a title.")

        source_index = chapter_data.get("source_heading_index")
        source_section = lookup.get(source_index)

        chapter = Chapter.objects.create(
            document=document,
            title=chapter_title,
            order=chapter_order,
            source_heading_index=source_index if source_section else None,
            source_text=(
                source_section.get("source_text", "")
                if source_section
                else str(chapter_data.get("source_text") or "")
            ),
            start_page=(
                source_section.get("start_page")
                if source_section
                else chapter_data.get("start_page")
            ),
            end_page=(
                source_section.get("end_page")
                if source_section
                else chapter_data.get("end_page")
            ),
            is_user_edited=user_edited,
        )

        for module_order, module_data in enumerate(modules, start=1):
            module_title = _clean_title(module_data.get("title"))
            if not module_title:
                raise ValueError(
                    f'Module {module_order} in "{chapter_title}" needs a title.'
                )

            module_source_index = module_data.get("source_heading_index")
            module_source = lookup.get(module_source_index)

            mod_source_text = (
                module_source.get("source_text", "")
                if module_source
                else str(module_data.get("source_text") or "")
            )
            mod_start_page = (
                module_source.get("start_page")
                if module_source
                else module_data.get("start_page")
            )
            mod_end_page = (
                module_source.get("end_page")
                if module_source
                else module_data.get("end_page")
            )

            # Persist LearningModule
            LearningModule.objects.create(
                chapter=chapter,
                title=module_title,
                order=module_order,
                source_heading_index=(
                    module_source_index if module_source else None
                ),
                source_text=mod_source_text,
                start_page=mod_start_page,
                end_page=mod_end_page,
                is_user_edited=user_edited,
            )

            # Also create corresponding MicroModule so tutoring & assessments can seamlessly reference it
            MicroModule.objects.create(
                chapter=chapter,
                document=document,
                title=module_title,
                order=module_order,
                source_text=mod_source_text,
                start_page=mod_start_page,
                end_page=mod_end_page,
                is_user_edited=user_edited,
            )

    document.title = _clean_title(outline.get("document_title")) or document.title
    document.save(update_fields=["title", "updated_at"])
