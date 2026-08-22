from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Conversation, Message
from .serializers import ConversationSerializer
from .services.tutor_service import teach_micro_module
from .services.question_answer_service import ask_question


class TeachMicroModuleView(APIView):

    def post(self, request):
        micro_module = request.data.get("micro_module")

        if not micro_module:
            return Response(
                {"detail": "micro_module is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        required_fields = ["id", "title", "source_text"]

        for field in required_fields:
            if not micro_module.get(field):
                return Response(
                    {"detail": f"{field} is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            result = teach_micro_module(micro_module)

            return Response({
                "micro_module_id": micro_module["id"],
                "title": micro_module["title"],
                **result,
                "source": {
                    "start_page": micro_module.get("start_page"),
                    "end_page": micro_module.get("end_page")
                }
            })

        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AskQuestionView(APIView):

    def post(self, request):
        question = request.data.get("question")
        conversation_id = request.data.get("conversation_id")
        micro_module = request.data.get("micro_module")
        explicit_history = request.data.get("conversation_history")

        if not question or not str(question).strip():
            return Response(
                {"detail": "question is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        cleaned_question = str(question).strip()
        conversation = None

        # Option B: Continuing an existing conversation
        if conversation_id:
            try:
                conversation = Conversation.objects.get(pk=conversation_id)
            except (Conversation.DoesNotExist, ValueError):
                return Response(
                    {"detail": "Conversation not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Reconstruct micro_module if not explicitly provided
            if not micro_module:
                micro_module = {
                    "id": conversation.micro_module_id,
                    "title": conversation.micro_module_title,
                    "source_text": conversation.source_text,
                    "start_page": conversation.start_page,
                    "end_page": conversation.end_page,
                }
        else:
            # Starting a new conversation: micro_module is required
            if not micro_module:
                return Response(
                    {"detail": "micro_module is required when starting a new conversation."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        required_fields = ["id", "title", "source_text"]
        for field in required_fields:
            if not micro_module.get(field):
                return Response(
                    {"detail": f"{field} is required in micro_module"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # If starting new conversation, create record in SQLite
        if not conversation:
            conversation = Conversation.objects.create(
                micro_module_id=str(micro_module["id"]),
                micro_module_title=str(micro_module.get("title", "")),
                source_text=str(micro_module.get("source_text", "")),
                start_page=micro_module.get("start_page"),
                end_page=micro_module.get("end_page"),
            )

        # Load recent conversation history (last 10 turns)
        if explicit_history and isinstance(explicit_history, list):
            history_payload = explicit_history
        else:
            past_messages = conversation.messages.order_by("created_at")[:10]
            history_payload = [
                {"role": msg.role, "content": msg.content}
                for msg in past_messages
            ]

        try:
            result = ask_question(
                micro_module=micro_module,
                question=cleaned_question,
                conversation_history=history_payload,
            )

            # Record student question and tutor answer
            student_msg = Message.objects.create(
                conversation=conversation,
                role=Message.Role.STUDENT,
                content=cleaned_question,
            )

            tutor_msg = Message.objects.create(
                conversation=conversation,
                role=Message.Role.TUTOR,
                content=result.get("answer", ""),
                answer_status=result.get("answer_status", "answered"),
                key_points=result.get("key_points", []),
            )

            # Touch conversation updated_at
            conversation.save(update_fields=["updated_at"])

            return Response({
                "conversation_id": str(conversation.id),
                "micro_module_id": micro_module["id"],
                "title": micro_module["title"],
                "question": cleaned_question,
                "answer_status": result.get("answer_status", "answered"),
                "answer": result.get("answer", ""),
                "key_points": result.get("key_points", []),
                "source": {
                    "start_page": micro_module.get("start_page"),
                    "end_page": micro_module.get("end_page")
                },
                "student_message_id": str(student_msg.id),
                "tutor_message_id": str(tutor_msg.id),
            })

        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConversationDetailView(APIView):

    def get(self, request, conversation_id):
        try:
            conversation = Conversation.objects.prefetch_related("messages").get(pk=conversation_id)
        except (Conversation.DoesNotExist, ValueError):
            return Response(
                {"detail": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(ConversationSerializer(conversation).data)
