import json
import requests
from django.conf import settings
from learning.models import AssessmentAttempt, MicroModule

OLLAMA_BASE_URL = getattr(settings, "LOCALMIND_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_URL = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"
MODEL = getattr(settings, "LOCALMIND_TUTOR_MODEL", "qwen3:1.7b")

REMEDIATION_SCHEMA = {
    "type": "object",
    "properties": {
        "missed_concepts_summary": {
            "type": "array",
            "items": {"type": "string"}
        },
        "remediation_explanation": {
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
        "key_takeaways_to_remember": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": [
        "missed_concepts_summary",
        "remediation_explanation",
        "key_takeaways_to_remember"
    ]
}


def generate_remediation_lesson(assessment_attempt_id=None, micro_module_id=None):
    """
    Generate a focused remediation review lesson for missed questions on an assessment attempt.
    """
    attempt = None
    if assessment_attempt_id:
        try:
            attempt = AssessmentAttempt.objects.select_related("assessment__micro_module").get(pk=assessment_attempt_id)
        except (AssessmentAttempt.DoesNotExist, ValueError):
            pass

    if not attempt and micro_module_id:
        try:
            attempt = AssessmentAttempt.objects.filter(
                assessment__micro_module_id=micro_module_id
            ).order_by("-created_at").first()
        except ValueError:
            pass

    if not attempt:
        raise ValueError("Valid assessment_attempt_id or micro_module_id with attempt history is required.")

    assessment = attempt.assessment
    micro_module = assessment.micro_module
    source_text = assessment.source_text or (micro_module.source_text if micro_module else "")
    title = assessment.title or (micro_module.title if micro_module else "Remediation Lesson")

    detailed_results = attempt.detailed_results or []
    failed_questions = [r for r in detailed_results if not r.get("is_correct", False)]

    if not failed_questions:
        # If student passed with 100%, return positive reinforcement summary
        return {
            "micro_module_id": str(micro_module.id) if micro_module else "",
            "title": title,
            "missed_concepts_summary": ["No concepts were missed! Excellent work."],
            "remediation_explanation": [
                {
                    "heading": "Mastery Confirmed",
                    "content": f"You scored {attempt.score}/{attempt.total_questions} ({attempt.percentage}%). You have mastered this micro-module."
                }
            ],
            "key_takeaways_to_remember": [
                "Review complete.",
                "You are ready to progress to the next micro-module."
            ]
        }

    formatted_missed = []
    for idx, f in enumerate(failed_questions, 1):
        q_text = f.get("question", "")
        q_type = f.get("type", "mcq")
        if q_type == "subjective":
            rubric = f.get("expected_rubric", "")
            student_ans = f.get("student_answer", "")
            feedback = f.get("feedback", "")
            formatted_missed.append(
                f"Missed Concept {idx} ({q_type.upper()}):\n"
                f"  Question: {q_text}\n"
                f"  Student's Answer: {student_ans}\n"
                f"  Required Fact/Rubric: {rubric}\n"
                f"  Evaluator Feedback: {feedback}"
            )
        else:
            correct_opt = f.get("correct_option", "")
            selected_opt = f.get("selected_option", "")
            explanation = f.get("explanation", "")
            formatted_missed.append(
                f"Missed Question {idx} (MCQ):\n"
                f"  Question: {q_text}\n"
                f"  Selected: {selected_opt} | Correct: {correct_opt}\n"
                f"  Explanation: {explanation}"
            )

    missed_block = "\n\n".join(formatted_missed)

    system_prompt = (
        "You are LocalMind, a patient and precise tutor conducting a targeted remediation review. "
        "Your task is to explain ONLY the concepts that the student missed on their recent test. "
        "CRITICAL RULES:\n"
        "1. Base your explanation SOLELY on the provided SOURCE TEXT.\n"
        "2. Do NOT introduce outside facts, unmentioned examples, cars, rockets, or external trivia.\n"
        "3. Focus on clarifying why the correct answer is right and correcting the student's misunderstanding.\n"
        "4. Keep the explanation simple, encouraging, and directly grounded in the text."
    )

    user_prompt = f"""
TITLE: {title}

SOURCE TEXT:
\"\"\"{source_text}\"\"\"

MISSED TEST QUESTIONS & CONCEPTS:
{missed_block}

TASK:
Write a focused remediation review lesson that explains ONLY the concepts missed by the student above.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "format": REMEDIATION_SCHEMA,
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

    parsed["micro_module_id"] = str(micro_module.id) if micro_module else ""
    parsed["title"] = title
    parsed["attempt_score"] = f"{attempt.score}/{attempt.total_questions} ({attempt.percentage}%)"

    return parsed
