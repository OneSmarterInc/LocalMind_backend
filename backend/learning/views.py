from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Assessment, AssessmentAttempt, MicroModule
from .serializers import (
    AssessmentAttemptSerializer,
    AssessmentSerializer,
    MicroModuleSerializer,
)
from .services.assessment_service import generate_assessment_questions
from .services.scoring_service import grade_assessment_attempt


class MicroModuleListCreateView(APIView):

    def get(self, request):
        micro_modules = MicroModule.objects.all()
        return Response(MicroModuleSerializer(micro_modules, many=True).data)

    def post(self, request):
        serializer = MicroModuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        micro_module = serializer.save()
        return Response(MicroModuleSerializer(micro_module).data, status=status.HTTP_201_CREATED)


class MicroModuleDetailView(APIView):

    def get(self, request, micro_module_id):
        try:
            micro_module = MicroModule.objects.get(pk=micro_module_id)
            return Response(MicroModuleSerializer(micro_module).data)
        except MicroModule.DoesNotExist:
            return Response({"detail": "MicroModule not found."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, micro_module_id):
        try:
            micro_module = MicroModule.objects.get(pk=micro_module_id)
        except MicroModule.DoesNotExist:
            return Response({"detail": "MicroModule not found."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("status")
        if new_status and new_status in MicroModule.Status.values:
            micro_module.status = new_status
            if new_status == MicroModule.Status.IN_PROGRESS and not micro_module.started_at:
                micro_module.started_at = timezone.now()
            elif new_status == MicroModule.Status.COMPLETED and not micro_module.completed_at:
                micro_module.completed_at = timezone.now()
            micro_module.save()

        return Response(MicroModuleSerializer(micro_module).data)


from .services.remediation_service import generate_remediation_lesson


class AssessmentGenerateView(APIView):

    def post(self, request):
        micro_module_data = request.data.get("micro_module")
        micro_module_id = request.data.get("micro_module_id")
        num_mcqs = request.data.get("num_mcqs", 5)
        num_subjective = request.data.get("num_subjective", 2)
        pass_percentage = request.data.get("pass_percentage", 70)

        source_text = ""
        title = ""
        micro_module = None
        micro_module_ref = ""
        previous_questions = []

        # Option A: Loaded from Database
        if micro_module_id:
            try:
                micro_module = MicroModule.objects.get(pk=micro_module_id)
                source_text = micro_module.source_text
                title = micro_module.title
                micro_module_ref = str(micro_module.id)

                # Fetch questions asked in past assessments for this micro-module to avoid duplicates
                past_assessments = Assessment.objects.filter(micro_module=micro_module)
                for past_ass in past_assessments:
                    for q in (past_ass.questions_data or []):
                        if q.get("question"):
                            previous_questions.append(q["question"])

                # Set status to in_progress if not started
                if micro_module.status == MicroModule.Status.NOT_STARTED:
                    micro_module.status = MicroModule.Status.IN_PROGRESS
                    micro_module.started_at = timezone.now()
                    micro_module.save(update_fields=["status", "started_at", "updated_at"])

            except (MicroModule.DoesNotExist, ValueError):
                return Response({"detail": "MicroModule not found."}, status=status.HTTP_404_NOT_FOUND)

        # Option B: Passed directly in payload
        elif micro_module_data:
            source_text = micro_module_data.get("source_text", "")
            title = micro_module_data.get("title", "")
            micro_module_ref = str(micro_module_data.get("id", ""))

            # Fetch previous questions if micro_module_ref matches past assessments
            if micro_module_ref:
                past_assessments = Assessment.objects.filter(micro_module_id_ref=micro_module_ref)
                for past_ass in past_assessments:
                    for q in (past_ass.questions_data or []):
                        if q.get("question"):
                            previous_questions.append(q["question"])
        else:
            return Response(
                {"detail": "Either micro_module_id or micro_module payload is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not source_text or not source_text.strip():
            return Response(
                {"detail": "source_text is required to generate assessment questions."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            questions = generate_assessment_questions(
                source_text=source_text.strip(),
                title=title,
                num_mcqs=int(num_mcqs),
                num_subjective=int(num_subjective),
                previous_questions=previous_questions
            )

            assessment = Assessment.objects.create(
                micro_module=micro_module,
                micro_module_id_ref=micro_module_ref,
                title=title or "Assessment",
                source_text=source_text,
                questions_data=questions,
                pass_percentage=int(pass_percentage)
            )

            return Response(
                AssessmentSerializer(assessment).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AssessmentDetailView(APIView):

    def get(self, request, assessment_id):
        try:
            assessment = Assessment.objects.get(pk=assessment_id)
            return Response(AssessmentSerializer(assessment).data)
        except (Assessment.DoesNotExist, ValueError):
            return Response({"detail": "Assessment not found."}, status=status.HTTP_404_NOT_FOUND)


class AssessmentSubmitView(APIView):

    def post(self, request, assessment_id):
        submitted_answers = request.data.get("submitted_answers")

        if submitted_answers is None or not isinstance(submitted_answers, dict):
            return Response(
                {"detail": "submitted_answers dictionary is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            assessment = Assessment.objects.get(pk=assessment_id)
        except (Assessment.DoesNotExist, ValueError):
            return Response({"detail": "Assessment not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            attempt = grade_assessment_attempt(assessment, submitted_answers)

            response_data = AssessmentAttemptSerializer(attempt).data
            if assessment.micro_module:
                response_data["micro_module_status"] = assessment.micro_module.status

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RemediationGenerateView(APIView):

    def post(self, request):
        assessment_attempt_id = request.data.get("assessment_attempt_id")
        micro_module_id = request.data.get("micro_module_id")

        if not assessment_attempt_id and not micro_module_id:
            return Response(
                {"detail": "Either assessment_attempt_id or micro_module_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            remediation_lesson = generate_remediation_lesson(
                assessment_attempt_id=assessment_attempt_id,
                micro_module_id=micro_module_id
            )
            return Response(remediation_lesson, status=status.HTTP_200_OK)

        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

