import json
import requests
from django.conf import settings

OLLAMA_BASE_URL = getattr(settings, "LOCALMIND_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_URL = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"
MODEL = getattr(settings, "LOCALMIND_TUTOR_MODEL", "qwen3:1.7b")

HYBRID_ASSESSMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "mcq_questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string"},
                    "question": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "key": {"type": "string"},
                                "text": {"type": "string"}
                            },
                            "required": ["key", "text"]
                        },
                        "minItems": 4,
                        "maxItems": 4
                    },
                    "correct_answer": {"type": "string"},
                    "explanation": {"type": "string"},
                    "source_reference": {"type": "string"}
                },
                "required": [
                    "id",
                    "type",
                    "question",
                    "options",
                    "correct_answer",
                    "explanation",
                    "source_reference"
                ]
            },
            "minItems": 5,
            "maxItems": 5
        },
        "subjective_questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string"},
                    "question": {"type": "string"},
                    "expected_rubric": {"type": "string"},
                    "source_reference": {"type": "string"}
                },
                "required": [
                    "id",
                    "type",
                    "question",
                    "expected_rubric",
                    "source_reference"
                ]
            },
            "minItems": 2,
            "maxItems": 2
        }
    },
    "required": ["mcq_questions", "subjective_questions"]
}


def generate_assessment_questions(source_text, title="", num_mcqs=5, num_subjective=2, previous_questions=None):
    """
    Generate hybrid assessment questions (5 MCQs + 2 Subjective questions)
    grounded strictly in source_text.

    If previous_questions is provided, instructs Ollama to generate fresh,
    non-overlapping questions.
    """
    exclusion_text = ""
    if previous_questions and isinstance(previous_questions, list) and len(previous_questions) > 0:
        prev_list_str = "\n".join(f"- {q}" for q in previous_questions[:20])
        exclusion_text = f"\nEXCLUDE PREVIOUS QUESTIONS:\nDo NOT repeat or rephrase any of these previously asked questions:\n{prev_list_str}\nGenerate fresh questions testing different factual details or angles of the text.\n"

    system_prompt = (
        "You are a strict, factual exam generator for students. "
        "Generate hybrid assessment questions (MCQs and Subjective questions) grounded SOLELY in the provided SOURCE TEXT. "
        "CRITICAL RULES:\n"
        "1. Every question, option, correct answer, rubric, and source_reference must be strictly based on facts written in the SOURCE TEXT.\n"
        "2. Do NOT invent outside knowledge, trivia, or facts not in the text.\n"
        "3. Provide exactly 5 Multiple Choice Questions (mcq_questions) with 4 options each ('A', 'B', 'C', 'D'). Set type to 'mcq'.\n"
        "4. Provide exactly 2 Subjective Questions (subjective_questions) asking for conceptual explanation in student's own words. Set type to 'subjective'.\n"
        "5. For subjective questions, provide an 'expected_rubric' stating the key factual points required for full credit."
    )

    user_prompt = f"""
TITLE: {title}

SOURCE TEXT:
\"\"\"{source_text}\"\"\"
{exclusion_text}
TASK:
Generate exactly {num_mcqs} Multiple Choice Questions (mcq_questions) AND exactly {num_subjective} Subjective Questions (subjective_questions) to test comprehension of the SOURCE TEXT above.

STRICT CONSTRAINTS:
1. All questions must test factual points explicitly stated in the SOURCE TEXT.
2. For mcq_questions (q1 to q5):
   - Provide 4 options ('A', 'B', 'C', 'D').
   - 'correct_answer' must be one of 'A', 'B', 'C', 'D'.
3. For subjective_questions (s1, s2):
   - Ask for short conceptual explanations.
   - 'expected_rubric': List the specific factual points from the text that a correct answer must include.
4. 'source_reference': Quote or cite the exact statement from the text.
"""


    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "format": HYBRID_ASSESSMENT_SCHEMA,
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
    parsed = json.loads(payload["message"]["content"])

    mcqs = parsed.get("mcq_questions", [])
    subjectives = parsed.get("subjective_questions", [])

    # Ensure IDs and types are clean
    for idx, q in enumerate(mcqs, 1):
        q["id"] = f"q{idx}"
        q["type"] = "mcq"

    for idx, q in enumerate(subjectives, 1):
        q["id"] = f"s{idx}"
        q["type"] = "subjective"

    return mcqs + subjectives
