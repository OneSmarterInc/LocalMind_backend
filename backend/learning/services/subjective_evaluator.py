import json
import requests
from django.conf import settings

OLLAMA_BASE_URL = getattr(settings, "LOCALMIND_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_URL = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"
MODEL = getattr(settings, "LOCALMIND_TUTOR_MODEL", "qwen3:1.7b")

EVALUATION_SCHEMA = {
    "type": "object",
    "properties": {
        "is_correct": {"type": "boolean"},
        "score_awarded": {"type": "number"},
        "feedback": {"type": "string"},
        "missing_points": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["is_correct", "score_awarded", "feedback", "missing_points"]
}


def evaluate_subjective_answer(source_text, question, expected_rubric, student_answer):
    """
    Evaluate a student's open-ended subjective response grounded in source_text & expected_rubric.

    Returns:
      {
        "is_correct": bool,
        "score_awarded": 1.0 or 0.0,
        "feedback": str,
        "missing_points": list
      }
    """
    if not student_answer or not str(student_answer).strip():
        return {
            "is_correct": False,
            "score_awarded": 0.0,
            "feedback": "No answer was provided for this question.",
            "missing_points": ["Student left the question blank."]
        }

    system_prompt = (
        "You are a strict, impartial exam evaluator. "
        "Your task is to judge whether a student's written response correctly answers the question "
        "based SOLELY on the supplied SOURCE TEXT and EXPECTED RUBRIC. "
        "CRITICAL RULES:\n"
        "1. Compare the student's answer against the SOURCE TEXT and EXPECTED RUBRIC.\n"
        "2. The student does NOT need to quote word-for-word, but MUST express the correct factual meaning.\n"
        "3. If the student's answer contains factually false statements according to the SOURCE TEXT, or misses the core concept, set is_correct to false and score_awarded to 0.0.\n"
        "4. If the answer correctly conveys the required factual concept from the text, set is_correct to true and score_awarded to 1.0.\n"
        "5. Provide constructive, brief feedback and list any missing_points."
    )

    user_prompt = f"""
SOURCE TEXT:
\"\"\"{source_text}\"\"\"

QUESTION:
{question}

EXPECTED RUBRIC / KEY POINTS:
{expected_rubric}

STUDENT ANSWER:
\"\"\"{student_answer}\"\"\"

TASK:
Evaluate the student's answer strictly based on the SOURCE TEXT and RUBRIC.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "format": EVALUATION_SCHEMA,
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
        payload = response.json()
        result = json.loads(payload["message"]["content"])

        # Enforce bounds
        is_correct = bool(result.get("is_correct", False))
        score = 1.0 if is_correct else 0.0

        return {
            "is_correct": is_correct,
            "score_awarded": score,
            "feedback": result.get("feedback", ""),
            "missing_points": result.get("missing_points", [])
        }

    except Exception as exc:
        # Fallback if evaluation fails: conservative default
        return {
            "is_correct": False,
            "score_awarded": 0.0,
            "feedback": f"Evaluation fallback due to error: {str(exc)}",
            "missing_points": ["Could not evaluate response automatically."]
        }
