import json
import requests
from django.conf import settings

OLLAMA_BASE_URL = getattr(settings, "LOCALMIND_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_URL = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"
MODEL = getattr(settings, "LOCALMIND_TUTOR_MODEL", "qwen3:1.7b")




def teach_micro_module(micro_module):

    schema = {
        "type": "object",
        "properties": {
            "introduction": {
                "type": "string"
            },
            "explanation": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "heading": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["heading", "content"]
                }
            },
            "application": {
                "type": "string"
            },
            "key_takeaways": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 3
            }
        },
        "required": [
            "introduction",
            "explanation",
            "application",
            "key_takeaways"
        ]
    }

    title = micro_module.get("title", "")
    source_text = micro_module.get("source_text", "")

    system_prompt = (
        "You are a strict, faithful textbook rewriter and educator. "
        "Your task is to rephrase and explain the supplied SOURCE TEXT in simple, clear language for a student. "
        "ABSOLUTE CONSTRAINTS:\n"
        "1. You must ONLY use facts, concepts, and definitions that are explicitly written in the SOURCE TEXT.\n"
        "2. FORBIDDEN: You must NEVER introduce any external examples, analogies, scenarios, or real-world objects "
        "(such as cars, vehicles, seatbelts, sports, balls, rockets, elevators, tables, etc.) unless they are explicitly in the SOURCE TEXT.\n"
        "3. FORBIDDEN: Do NOT introduce outside scientific or technical concepts (e.g. mass, gravity, friction, acceleration, types of inertia) "
        "unless they are explicitly written in the SOURCE TEXT.\n"
        "4. If no application is mentioned in the SOURCE TEXT, leave 'application' as an empty string \"\".\n"
        "5. Explain only what is in the text. If the text is short, keep the explanation concise and faithful. Do not invent new sections."
    )

    user_prompt = f"""
TITLE:
{title}

SOURCE TEXT:
\"\"\"{source_text}\"\"\"

TASK:
Explain and simplify the concepts contained SOLELY in the SOURCE TEXT above.

STRICT CONSTRAINTS:
1. Explain only the facts and sentences stated in the SOURCE TEXT.
2. NO EXTERNAL EXAMPLES: Do not invent examples or scenarios not written in the text.
3. NO EXTERNAL CONCEPTS: Do not introduce outside knowledge or unmentioned details.
4. "introduction": 1-2 sentence overview strictly derived from the text.
5. "explanation": 1-3 sections explaining only what is stated in the text.
6. "application": Keep empty "" unless an application is explicitly named in the text.
7. "key_takeaways": Exactly 3 bullet points directly summarizing the text.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "format": schema,
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.0,
                "top_p": 0.1
            },
            "keep_alive": "30m"
        },
        timeout=90
    )

    response.raise_for_status()

    return json.loads(
        response.json()["message"]["content"]
    )