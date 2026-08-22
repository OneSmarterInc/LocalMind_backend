from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from tutor.services.question_answer_service import ask_question, NOT_IN_SOURCE_DEFAULT_TEXT


class TutorTeachApiTests(TestCase):

    def setUp(self):
        self.url = reverse("teach-micro-module")
        self.valid_payload = {
            "micro_module": {
                "id": "a8c220b2-868f-488c-bc86-174d2fa3aaff",
                "document_id": "9b5a0f50-277a-479a-84d7-1b903b582ae2",
                "title": "Newton's First Law",
                "order": 1,
                "source_text": "An object at rest stays at rest and an object in motion stays in motion with the same speed and in the same direction unless acted upon by an unbalanced external force.",
                "start_page": 1,
                "end_page": 2,
            }
        }

    def test_missing_micro_module_payload(self):
        response = self.client.post(self.url, {}, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("micro_module is required", response.json()["detail"])

    def test_missing_required_fields(self):
        invalid_payload = {
            "micro_module": {
                "id": "a8c220b2-868f-488c-bc86-174d2fa3aaff",
                # missing title and source_text
            }
        }
        response = self.client.post(self.url, invalid_payload, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    @patch("tutor.views.teach_micro_module")
    def test_successful_teach(self, mock_teach):
        mock_teach.return_value = {
            "introduction": "Newton's First Law describes the natural tendency of objects to maintain their state of motion.",
            "explanation": [
                {
                    "heading": "State of Rest and Motion",
                    "content": "An object maintains its velocity unless an external force intervenes."
                }
            ],
            "application": "",
            "key_takeaways": [
                "Objects keep their current motion without net force.",
                "External unbalanced force is required to change motion.",
                "This principle defines inertia."
            ]
        }

        response = self.client.post(self.url, self.valid_payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["micro_module_id"], "a8c220b2-868f-488c-bc86-174d2fa3aaff")
        self.assertEqual(data["title"], "Newton's First Law")
        self.assertEqual(len(data["explanation"]), 1)
        self.assertEqual(len(data["key_takeaways"]), 3)
        self.assertEqual(data["source"]["start_page"], 1)
        self.assertEqual(data["source"]["end_page"], 2)


class TutorAskApiTests(TestCase):

    def setUp(self):
        self.url = reverse("ask-question")
        self.valid_payload = {
            "micro_module": {
                "id": "a8c220b2-868f-488c-bc86-174d2fa3aaff",
                "title": "Newton's First Law",
                "source_text": "An object at rest stays at rest and an object in motion stays in motion with the same speed and in the same direction unless acted upon by an unbalanced external force.",
                "start_page": 1,
                "end_page": 2,
            },
            "question": "What happens to an object at rest without an external force?"
        }

    def test_missing_question_or_module(self):
        res1 = self.client.post(self.url, {"question": "What is force?"}, content_type="application/json")
        self.assertEqual(res1.status_code, 400)

        res2 = self.client.post(self.url, {"micro_module": self.valid_payload["micro_module"]}, content_type="application/json")
        self.assertEqual(res2.status_code, 400)

    @patch("tutor.views.ask_question")
    def test_ask_question_answered(self, mock_ask):
        mock_ask.return_value = {
            "answer_status": "answered",
            "answer": "According to the source material, an object at rest will remain at rest unless an unbalanced external force acts on it.",
            "key_points": [
                "Objects remain at rest in the absence of an unbalanced external force."
            ]
        }

        response = self.client.post(self.url, self.valid_payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["micro_module_id"], "a8c220b2-868f-488c-bc86-174d2fa3aaff")
        self.assertEqual(data["answer_status"], "answered")
        self.assertIn("remain at rest", data["answer"])
        self.assertEqual(len(data["key_points"]), 1)
        self.assertEqual(data["source"]["start_page"], 1)

    @patch("tutor.views.ask_question")
    def test_ask_question_creates_conversation_and_messages(self, mock_ask):
        mock_ask.return_value = {
            "answer_status": "answered",
            "answer": "An object at rest stays at rest unless an external force acts.",
            "key_points": ["Inertia maintains rest state."]
        }

        response = self.client.post(self.url, self.valid_payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("conversation_id", data)
        self.assertIn("student_message_id", data)
        self.assertIn("tutor_message_id", data)

        from tutor.models import Conversation, Message
        conv = Conversation.objects.get(pk=data["conversation_id"])
        self.assertEqual(conv.micro_module_id, "a8c220b2-868f-488c-bc86-174d2fa3aaff")
        self.assertEqual(conv.messages.count(), 2)

        student_msg = conv.messages.filter(role=Message.Role.STUDENT).first()
        tutor_msg = conv.messages.filter(role=Message.Role.TUTOR).first()
        self.assertEqual(student_msg.content, "What happens to an object at rest without an external force?")
        self.assertEqual(tutor_msg.content, "An object at rest stays at rest unless an external force acts.")

    @patch("tutor.views.ask_question")
    def test_ask_question_not_in_source(self, mock_ask):
        mock_ask.return_value = {
            "answer_status": "not_in_source",
            "answer": NOT_IN_SOURCE_DEFAULT_TEXT,
            "key_points": []
        }

        unsupported_payload = {
            "micro_module": self.valid_payload["micro_module"],
            "question": "What is the fuel capacity of a Falcon 9 rocket?"
        }

        response = self.client.post(self.url, unsupported_payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["answer_status"], "not_in_source")
        self.assertEqual(data["answer"], NOT_IN_SOURCE_DEFAULT_TEXT)
        self.assertEqual(data["key_points"], [])


    @patch("tutor.views.ask_question")
    def test_followup_question_option_b_without_micro_module(self, mock_ask):
        from tutor.models import Conversation
        conv = Conversation.objects.create(
            micro_module_id="a8c220b2-868f-488c-bc86-174d2fa3aaff",
            micro_module_title="Newton's First Law",
            source_text="An object at rest stays at rest unless acted upon by an unbalanced force.",
            start_page=1,
            end_page=2,
        )

        mock_ask.return_value = {
            "answer_status": "answered",
            "answer": "It means the object will not start moving on its own.",
            "key_points": ["Objects need a force to move."]
        }

        # Follow up question sending ONLY conversation_id and question (Option B)
        followup_payload = {
            "conversation_id": str(conv.id),
            "question": "Can you explain that more simply?"
        }

        response = self.client.post(self.url, followup_payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["conversation_id"], str(conv.id))
        self.assertEqual(data["title"], "Newton's First Law")
        self.assertEqual(conv.messages.count(), 2)

        # Verify ask_question was called with the DB-stored source text
        args, kwargs = mock_ask.call_args
        self.assertEqual(kwargs["micro_module"]["source_text"], "An object at rest stays at rest unless acted upon by an unbalanced force.")

    def test_conversation_detail_get_endpoint(self):
        from tutor.models import Conversation, Message
        conv = Conversation.objects.create(
            micro_module_id="mm-123",
            micro_module_title="Inertia",
            source_text="Some text",
        )
        Message.objects.create(conversation=conv, role=Message.Role.STUDENT, content="What is inertia?")
        Message.objects.create(conversation=conv, role=Message.Role.TUTOR, content="It is resistance to motion change.", answer_status="answered")

        detail_url = reverse("conversation-detail", kwargs={"conversation_id": conv.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], str(conv.id))
        self.assertEqual(data["micro_module_title"], "Inertia")
        self.assertEqual(len(data["messages"]), 2)

    def test_conversation_detail_not_found(self):
        import uuid
        detail_url = reverse("conversation-detail", kwargs={"conversation_id": uuid.uuid4()})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 404)



class QuestionAnswerServiceUnitTests(TestCase):

    @patch("tutor.services.question_answer_service.requests.post")
    def test_service_parses_ollama_answered(self, mock_post):
        mock_post.return_value.json.return_value = {
            "message": {
                "content": '{"answer_status": "answered", "answer": "Inertia keeps the object stationary.", "key_points": ["No external force means no state change."]}'
            }
        }
        mock_post.return_value.status_code = 200

        result = ask_question(
            micro_module={
                "id": "1",
                "title": "Inertia",
                "source_text": "An object at rest stays at rest."
            },
            question="What keeps the object at rest?"
        )

        self.assertEqual(result["answer_status"], "answered")
        self.assertEqual(result["answer"], "Inertia keeps the object stationary.")
        self.assertEqual(len(result["key_points"]), 1)

    @patch("tutor.services.question_answer_service.requests.post")
    def test_service_parses_ollama_not_in_source_fallback(self, mock_post):
        mock_post.return_value.json.return_value = {
            "message": {
                "content": '{"answer_status": "not_in_source", "answer": "", "key_points": ["some point"]}'
            }
        }
        mock_post.return_value.status_code = 200

        result = ask_question(
            micro_module={
                "id": "1",
                "title": "Inertia",
                "source_text": "An object at rest stays at rest."
            },
            question="What is the speed of light?"
        )

        self.assertEqual(result["answer_status"], "not_in_source")
        self.assertEqual(result["answer"], NOT_IN_SOURCE_DEFAULT_TEXT)
        self.assertEqual(result["key_points"], [])
