from django.utils import timezone
from learning.models import AssessmentAttempt, Chapter, MicroModule
from learning.services.subjective_evaluator import evaluate_subjective_answer


def grade_assessment_attempt(assessment, submitted_answers):
    """
    Score a hybrid assessment attempt (MCQs + Subjective questions).

    - MCQs (type="mcq"): Graded deterministically in Python.
    - Subjective (type="subjective"): Evaluated grounded in source_text & expected_rubric via LLM.
    - Calculates total score, percentage, passed boolean (percentage >= pass_percentage).
    - Updates associated MicroModule or Chapter status to 'completed' (if passed) or 'needs_review' (if failed).
    - Persists AssessmentAttempt record in SQLite.
    """
    questions = assessment.questions_data or []
    total_questions = len(questions)

    if total_questions == 0:
        raise ValueError("Cannot grade an assessment with no questions.")

    total_score = 0.0
    detailed_results = []

    # Resolve source text from assessment, micro_module, or chapter micro_modules
    source_text = assessment.source_text
    if not source_text:
        if assessment.micro_module:
            source_text = assessment.micro_module.source_text or ""
        elif assessment.chapter:
            source_text = assessment.chapter.source_text or "\n\n".join(
                mm.source_text for mm in assessment.chapter.micro_modules.all() if mm.source_text
            )

    for q in questions:
        q_id = str(q.get("id"))
        q_type = q.get("type", "mcq")

        if q_type == "subjective":
            student_text = str(submitted_answers.get(q_id, "")).strip()
            eval_res = evaluate_subjective_answer(
                source_text=source_text,
                question=q.get("question", ""),
                expected_rubric=q.get("expected_rubric", ""),
                student_answer=student_text
            )

            is_correct = eval_res.get("is_correct", False)
            score_awarded = eval_res.get("score_awarded", 1.0 if is_correct else 0.0)
            total_score += score_awarded

            detailed_results.append({
                "question_id": q_id,
                "type": "subjective",
                "question": q.get("question", ""),
                "student_answer": student_text,
                "expected_rubric": q.get("expected_rubric", ""),
                "is_correct": is_correct,
                "score_awarded": score_awarded,
                "feedback": eval_res.get("feedback", ""),
                "missing_points": eval_res.get("missing_points", []),
                "source_reference": q.get("source_reference", "")
            })

        else:
            # Default MCQ evaluation
            correct_opt = str(q.get("correct_answer", "")).upper()
            student_opt = str(submitted_answers.get(q_id, "")).upper()

            is_correct = (student_opt == correct_opt and bool(correct_opt))
            score_awarded = 1.0 if is_correct else 0.0
            total_score += score_awarded

            detailed_results.append({
                "question_id": q_id,
                "type": "mcq",
                "question": q.get("question", ""),
                "selected_option": student_opt,
                "correct_option": correct_opt,
                "is_correct": is_correct,
                "score_awarded": score_awarded,
                "explanation": q.get("explanation", ""),
                "source_reference": q.get("source_reference", "")
            })

    percentage = round((total_score / float(total_questions)) * 100.0, 1)
    pass_threshold = assessment.pass_percentage or 70
    passed = percentage >= pass_threshold

    # Record attempt in DB
    attempt = AssessmentAttempt.objects.create(
        assessment=assessment,
        submitted_answers=submitted_answers,
        score=int(total_score),
        total_questions=total_questions,
        percentage=percentage,
        passed=passed,
        detailed_results=detailed_results
    )

    # Update MicroModule progress status if micro_module is associated
    if assessment.micro_module:
        module = assessment.micro_module
        if passed:
            module.status = MicroModule.Status.COMPLETED
            if not module.completed_at:
                module.completed_at = timezone.now()
        else:
            module.status = MicroModule.Status.NEEDS_REVIEW

        module.save(update_fields=["status", "completed_at", "updated_at"])

        # If micro_module has a parent chapter, ensure chapter is at least in_progress
        if module.chapter and module.chapter.status == Chapter.Status.NOT_STARTED:
            module.chapter.status = Chapter.Status.IN_PROGRESS
            module.chapter.started_at = timezone.now()
            module.chapter.save(update_fields=["status", "started_at", "updated_at"])

    # Update Chapter progress status if chapter is associated directly
    if assessment.chapter:
        chapter = assessment.chapter
        if passed:
            chapter.status = Chapter.Status.COMPLETED
            if not chapter.completed_at:
                chapter.completed_at = timezone.now()
        else:
            chapter.status = Chapter.Status.NEEDS_REVIEW

        chapter.save(update_fields=["status", "completed_at", "updated_at"])

    return attempt

