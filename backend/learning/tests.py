from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from learning.models import Assessment, AssessmentAttempt, MicroModule
from learning.services.scoring_service import grade_assessment_attempt


SAMPLE_SOURCE_TEXT = "An object at rest stays at rest and an object in motion stays in motion with the same speed and in the same direction unless acted upon by an unbalanced external force. This tendency is known as inertia."

SAMPLE_QUESTIONS = [
    {
        "id": "q1",
        "type": "mcq",
        "question": "What stays at rest?",
        "options": [
            {"key": "A", "text": "An object at rest"},
            {"key": "B", "text": "A moving rocket"},
            {"key": "C", "text": "A rolling ball"},
            {"key": "D", "text": "Nothing"}
        ],
        "correct_answer": "A",
        "explanation": "The text states an object at rest stays at rest.",
        "source_reference": "An object at rest stays at rest"
    },
    {
        "id": "s1",
        "type": "subjective",
        "question": "Explain inertia based on the text.",
        "expected_rubric": "Inertia is the tendency of an object to remain at rest or in motion unless acted upon by an unbalanced external force.",
        "source_reference": "This tendency is known as inertia."
    }
]


class MicroModuleProgressTests(TestCase):

    def test_micromodule_initial_status(self):
        mm = MicroModule.objects.create(
            title="Newton's Laws",
            source_text="An object at rest stays at rest.",
        )
        self.assertEqual(mm.status, MicroModule.Status.NOT_STARTED)
        self.assertIsNone(mm.completed_at)

    def test_status_update_api(self):
        mm = MicroModule.objects.create(title="Inertia", source_text="Sample text")
        url = reverse("micro-module-status-update", kwargs={"micro_module_id": mm.id})
        res = self.client.patch(url, {"status": "in_progress"}, content_type="application/json")
        self.assertEqual(res.status_code, 200)
        mm.refresh_from_db()
        self.assertEqual(mm.status, MicroModule.Status.IN_PROGRESS)
        self.assertIsNotNone(mm.started_at)


class HybridScoringTests(TestCase):

    def setUp(self):
        self.mm = MicroModule.objects.create(
            title="Newton's First Law",
            source_text=SAMPLE_SOURCE_TEXT,
            status=MicroModule.Status.IN_PROGRESS,
        )
        self.assessment = Assessment.objects.create(
            micro_module=self.mm,
            title=self.mm.title,
            questions_data=SAMPLE_QUESTIONS,
            pass_percentage=70
        )

    @patch("learning.services.scoring_service.evaluate_subjective_answer")
    def test_passing_at_70_percent(self, mock_eval):
        mock_eval.return_value = {"is_correct": True, "score_awarded": 1.0, "feedback": "Correct.", "missing_points": []}
        submitted = {"q1": "A", "s1": "Inertia is the tendency to stay at rest or in motion."}
        attempt = grade_assessment_attempt(self.assessment, submitted)

        self.assertEqual(attempt.score, 2)
        self.assertEqual(attempt.percentage, 100.0)
        self.assertTrue(attempt.passed)
        self.mm.refresh_from_db()
        self.assertEqual(self.mm.status, MicroModule.Status.COMPLETED)
        self.assertIsNotNone(self.mm.completed_at)

    @patch("learning.services.scoring_service.evaluate_subjective_answer")
    def test_failing_below_70_percent(self, mock_eval):
        mock_eval.return_value = {"is_correct": False, "score_awarded": 0.0, "feedback": "Incomplete.", "missing_points": ["Missing external force."]}
        submitted = {"q1": "D", "s1": "I don't know."}
        attempt = grade_assessment_attempt(self.assessment, submitted)

        self.assertEqual(attempt.score, 0)
        self.assertEqual(attempt.percentage, 0.0)
        self.assertFalse(attempt.passed)
        self.mm.refresh_from_db()
        self.assertEqual(self.mm.status, MicroModule.Status.NEEDS_REVIEW)

    @patch("learning.services.scoring_service.evaluate_subjective_answer")
    def test_borderline_70_percent_passes(self, mock_eval):
        """2/2 = 100% for a test with 2 questions; 1/2 = 50% fails. Simulate a borderline pass."""
        # Create a 10-question assessment (7/10 = 70%) using only MCQs for deterministic test
        mcq_questions = [
            {"id": f"q{i}", "type": "mcq", "question": f"Q{i}", "options": [
                {"key": "A", "text": "Correct"}, {"key": "B", "text": "Wrong"},
                {"key": "C", "text": "Wrong"}, {"key": "D", "text": "Wrong"}
            ], "correct_answer": "A", "explanation": "", "source_reference": ""}
            for i in range(1, 11)
        ]
        assessment = Assessment.objects.create(
            micro_module=self.mm, title="Borderline", questions_data=mcq_questions, pass_percentage=70
        )
        # 7 correct out of 10 = 70.0% — exactly at threshold, should pass
        submitted = {f"q{i}": "A" if i <= 7 else "B" for i in range(1, 11)}
        attempt = grade_assessment_attempt(assessment, submitted)
        self.assertEqual(attempt.percentage, 70.0)
        self.assertTrue(attempt.passed)


class RemediationApiTests(TestCase):

    def setUp(self):
        self.mm = MicroModule.objects.create(
            title="Newton's First Law",
            source_text=SAMPLE_SOURCE_TEXT,
            status=MicroModule.Status.NEEDS_REVIEW,
        )
        self.assessment = Assessment.objects.create(
            micro_module=self.mm,
            title=self.mm.title,
            source_text=SAMPLE_SOURCE_TEXT,
            questions_data=SAMPLE_QUESTIONS,
            pass_percentage=70
        )

    @patch("learning.services.scoring_service.evaluate_subjective_answer")
    def test_remediation_generated_for_failed_attempt(self, mock_eval):
        mock_eval.return_value = {"is_correct": False, "score_awarded": 0.0, "feedback": "Wrong.", "missing_points": ["Force concept."]}

        # Create a failed attempt
        attempt = grade_assessment_attempt(self.assessment, {"q1": "D", "s1": "I don't know."})
        self.assertFalse(attempt.passed)

        url = reverse("remediation-generate")

        # Mock Ollama remediation call
        with patch("learning.services.remediation_service.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.raise_for_status = lambda: None
            mock_post.return_value.json.return_value = {
                "message": {
                    "content": '{"missed_concepts_summary": ["Inertia concept was missed"], "remediation_explanation": [{"heading": "Inertia Review", "content": "An object at rest stays at rest unless an external force acts."}], "key_takeaways_to_remember": ["Inertia = tendency to resist motion change"]}'
                }
            }

            res = self.client.post(
                url,
                {"assessment_attempt_id": str(attempt.id)},
                content_type="application/json"
            )

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("missed_concepts_summary", data)
        self.assertIn("remediation_explanation", data)
        self.assertIn("key_takeaways_to_remember", data)
        self.assertTrue(len(data["missed_concepts_summary"]) > 0)

    def test_remediation_by_micro_module_id_no_attempts(self):
        url = reverse("remediation-generate")
        res = self.client.post(
            url,
            {"micro_module_id": str(self.mm.id)},
            content_type="application/json"
        )
        # No attempt exists yet — should return 400
        self.assertEqual(res.status_code, 400)

    def test_remediation_missing_params_returns_400(self):
        url = reverse("remediation-generate")
        res = self.client.post(url, {}, content_type="application/json")
        self.assertEqual(res.status_code, 400)


class AssessmentFreshQuestionsTests(TestCase):

    def setUp(self):
        self.mm = MicroModule.objects.create(
            title="Newton's First Law",
            source_text=SAMPLE_SOURCE_TEXT,
        )

    @patch("learning.views.generate_assessment_questions")
    def test_previous_questions_passed_on_retest(self, mock_gen):
        # Set 1 from first assessment
        mock_gen.return_value = [
            {"id": "q1", "type": "mcq", "question": "What stays at rest?",
             "options": [{"key": "A", "text": "A"}, {"key": "B", "text": "B"}, {"key": "C", "text": "C"}, {"key": "D", "text": "D"}],
             "correct_answer": "A", "explanation": "", "source_reference": ""},
        ]

        url = reverse("assessment-generate")

        # First assessment
        self.client.post(url, {"micro_module_id": str(self.mm.id)}, content_type="application/json")

        # Second assessment (retest) — should pass previous questions
        self.client.post(url, {"micro_module_id": str(self.mm.id)}, content_type="application/json")

        self.assertEqual(mock_gen.call_count, 2)

        # Verify second call had non-empty previous_questions list
        second_call_kwargs = mock_gen.call_args_list[1][1]
        prev_q = second_call_kwargs.get("previous_questions", [])
        self.assertGreater(len(prev_q), 0)
        self.assertIn("What stays at rest?", prev_q)

    @patch("learning.views.generate_assessment_questions")
    def test_first_assessment_has_no_previous_questions(self, mock_gen):
        mock_gen.return_value = []
        url = reverse("assessment-generate")
        self.client.post(url, {"micro_module_id": str(self.mm.id)}, content_type="application/json")

        first_call_kwargs = mock_gen.call_args_list[0][1]
        prev_q = first_call_kwargs.get("previous_questions", [])
        self.assertEqual(prev_q, [])
