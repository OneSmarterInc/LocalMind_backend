from pathlib import Path
from django.db import transaction
from learning.models import LearningModule, Chapter
from .ollama import generate_outline_with_ollama

def _clean_title(value):
    return " ".join(str(value or "").split()).strip()

def _heuristic_outline(original_name, headings):
    """
    Safe fallback if Ollama is unavailable.

    Top-level detected headings become chapters and are grouped into
    learning modules of up to four chapters.
    """
    default_title = Path(original_name).stem

    if not headings:
        return {
            "document_title": default_title,
            "modules": [{
                "title": "Module 1",
                "chapters": [{"title": "Document Content"}],
            }],
        }

    min_level = min(item["level"] for item in headings)
    top = [
        _clean_title(item["title"])
        for item in headings
        if item["level"] == min_level and _clean_title(item["title"])
    ]

    # If there is only one top heading (often the book title),
    # use the next heading level for chapters.
    if len(top) <= 1:
        next_level = min_level + 1
        second_level = [
            _clean_title(item["title"])
            for item in headings
            if item["level"] == next_level and _clean_title(item["title"])
        ]
        if second_level:
            top = second_level

    if not top:
        top = [_clean_title(item["title"]) for item in headings[:20]]

    # Remove exact consecutive duplicates while preserving order.
    cleaned = []
    for title in top:
        if title and (not cleaned or cleaned[-1] != title):
            cleaned.append(title)

    modules = []
    chunk_size = 4
    for index in range(0, len(cleaned), chunk_size):
        chapters = cleaned[index:index + chunk_size]
        modules.append({
            "title": f"Module {len(modules) + 1}",
            "chapters": [{"title": title} for title in chapters],
        })

    return {
        "document_title": default_title,
        "modules": modules or [{
            "title": "Module 1",
            "chapters": [{"title": "Document Content"}],
        }],
    }

def build_proposed_outline(document, headings):
    ai_outline = generate_outline_with_ollama(document.original_name, headings)
    if ai_outline:
        return ai_outline, "ollama"

    return _heuristic_outline(document.original_name, headings), "heuristic"

@transaction.atomic
def replace_outline(document, outline, user_edited=False):
    modules = outline.get("modules") or []
    if not modules:
        raise ValueError("The outline must contain at least one module.")

    LearningModule.objects.filter(document=document).delete()

    for module_index, module_data in enumerate(modules, start=1):
        module_title = _clean_title(module_data.get("title"))
        chapters = module_data.get("chapters") or []

        if not module_title:
            raise ValueError(f"Module {module_index} needs a title.")

        if not chapters:
            raise ValueError(f'"{module_title}" must contain at least one chapter.')

        module = LearningModule.objects.create(
            document=document,
            title=module_title,
            order=module_index,
            is_user_edited=user_edited,
        )

        for chapter_index, chapter_data in enumerate(chapters, start=1):
            chapter_title = _clean_title(chapter_data.get("title"))
            if not chapter_title:
                raise ValueError(
                    f'Chapter {chapter_index} in "{module_title}" needs a title.'
                )

            Chapter.objects.create(
                module=module,
                title=chapter_title,
                order=chapter_index,
                is_user_edited=user_edited,
            )

    document.title = _clean_title(outline.get("document_title")) or document.title
    document.save(update_fields=["title", "updated_at"])
