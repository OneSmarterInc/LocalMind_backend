import json
import requests
from django.conf import settings

OLLAMA_BASE_URL = getattr(settings, "LOCALMIND_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_URL = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"
MODEL = getattr(settings, "LOCALMIND_TUTOR_MODEL", "qwen3:1.7b")

NOT_IN_SOURCE_DEFAULT_TEXT = "This detail is not covered in the current learning material."

QUESTION_ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer_status": {
            "type": "string",
            "enum": ["answered", "not_in_source"]
        },
        "answer": {
            "type": "string"
        },
        "key_points": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    },
    "required": [
        "answer_status",
        "answer",
        "key_points"
    ]
}


def ask_question(micro_module, question, conversation_history=None):
    """
    Answer a student's question grounded strictly in the micro-module's source text.

    If the question cannot be answered purely from the source material,
    returns answer_status="not_in_source".
    """
    title = micro_module.get("title", "")
    source_text = micro_module.get("source_text", "")

    history_text = ""
    if conversation_history:
        formatted_history = []
        for msg in conversation_history:
            role = "Student" if msg.get("role") == "student" else "Professor"
            content = msg.get("content", "")
            formatted_history.append(f"{role}: {content}")
        history_text = "\nRECENT CONVERSATION HISTORY:\n" + "\n".join(formatted_history) + "\n"

    system_prompt = (
        "You are LocalMind, a verbatim-grounded pedagogical assistant. "
        "Your sole task is to answer the student's question using ONLY facts explicitly present in the supplied SOURCE MATERIAL. "
        "CRITICAL RULES:\n"
        "1. You must NEVER introduce any fact, definition, property, scientific concept, or real-world example (e.g. cars, vehicles, rockets, sports, mass, gravity) that is not explicitly in the SOURCE MATERIAL.\n"
        "2. If the answer is not fully supported by the text, return answer_status: 'not_in_source'."
    )

    user_prompt = f"""
TITLE:
{title}

SOURCE MATERIAL:
\"\"\"{source_text}\"\"\"
{history_text}
STUDENT QUESTION:
{question}

Grounding and Answering Rules:
1. Every factual statement in your answer and key_points must be directly supported by the SOURCE MATERIAL above.
2. If the student question asks about something that is NOT covered or not explicitly stated in the SOURCE MATERIAL:
   - Set "answer_status" to "not_in_source"
   - Set "answer" to "{NOT_IN_SOURCE_DEFAULT_TEXT}"
   - Set "key_points" to []
3. If the question IS covered by the SOURCE MATERIAL:
   - Set "answer_status" to "answered"
   - Explain the answer clearly in simple words, using ONLY the facts from the source material.
   - Do NOT introduce unmentioned properties (such as mass, weight, gravity, or friction) unless they are in the SOURCE MATERIAL.
   - Do NOT invent real-world examples (no cars, rockets, balls, etc.) unless they are in the SOURCE MATERIAL.
   - Provide 1 to 3 concise key points drawn directly and solely from the source text.
4. Return only valid JSON matching the required schema.
""".strip()

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
            "format": QUESTION_ANSWER_SCHEMA,
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

    parsed = json.loads(response.json()["message"]["content"])

    # Enforce safe defaults if status is not_in_source
    if parsed.get("answer_status") == "not_in_source":
        if not parsed.get("answer") or parsed["answer"].strip() == "":
            parsed["answer"] = NOT_IN_SOURCE_DEFAULT_TEXT
        parsed["key_points"] = []
    elif parsed.get("answer_status") != "answered":
        parsed["answer_status"] = "answered"

    if "key_points" not in parsed or not isinstance(parsed["key_points"], list):
        parsed["key_points"] = []

    return parsed
