import json
import requests
from django.conf import settings

OUTLINE_SCHEMA = {
    "type": "object",
    "properties": {
        "document_title": {"type": "string"},
        "modules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "chapters": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"}
                            },
                            "required": ["title"],
                        },
                    },
                },
                "required": ["title", "chapters"],
            },
        },
    },
    "required": ["document_title", "modules"],
}

def generate_outline_with_ollama(original_name, headings):
    """
    Group detected headings into sensible learning modules and chapters.

    Only heading titles are sent to Ollama, not the entire book.
    """
    if not settings.LOCALMIND_USE_OLLAMA:
        return None

    if not headings:
        return None

    heading_text = "\n".join(
        f'Level {item["level"]}: {item["title"]}'
        for item in headings[:600]
    )

    prompt = f"""
You are organizing a student's uploaded learning material.

File name: {original_name}

Detected headings:
{heading_text}

Create a proposed learning outline.

Rules:
1. Preserve the source material's real chapter/section meaning.
2. Do not invent topics that are not represented by the headings.
3. Group related chapters/sections into logical learning modules.
4. Keep titles concise.
5. Keep the original order.
6. The student will review and edit this outline before tutoring starts.
7. Return only data matching the provided JSON schema.
""".strip()

    try:
        response = requests.post(
            f"{settings.LOCALMIND_OLLAMA_URL}/api/chat",
            json={
                "model": settings.LOCALMIND_OUTLINE_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Return a faithful course outline from document headings.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "format": OUTLINE_SCHEMA,
            },
            timeout=180,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["message"]["content"]
        parsed = json.loads(content)

        if not parsed.get("modules"):
            return None

        return parsed
    except (requests.RequestException, KeyError, ValueError, json.JSONDecodeError):
        return None
