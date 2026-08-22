from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Chapter, LearningModule, MicroModule, Assessment, AssessmentAttempt
from .services.assessment_service import generate_assessment_questions
from .services.scoring_service import grade_assessment_attempt
from .services.remediation_service import generate_remediation_lesson


class ChapterListView(APIView):
    def get(self, request):
        chapters = Chapter.objects.all()

        data = []
        for chapter in chapters:
            learning_modules = LearningModule.objects.filter(chapter=chapter)
            micro_modules = MicroModule.objects.filter(chapter=chapter)

            modules_list = [
                {
                    "id": str(m.id),
                    "title": m.title,
                    "order": m.order,
                    "status": m.status,
                    "source_text": m.source_text,
                    "start_page": m.start_page,
                    "end_page": m.end_page,
                    "chapter_id": str(chapter.id),
                }
                for m in learning_modules
            ]

            micro_modules_list = [
                {
                    "id": str(mm.id),
                    "title": mm.title,
                    "order": mm.order,
                    "status": mm.status,
                    "source_text": mm.source_text,
                    "start_page": mm.start_page,
                    "end_page": mm.end_page,
                    "chapter_id": str(chapter.id),
                }
                for mm in micro_modules
            ]

            data.append({
                "id": str(chapter.id),
                "title": chapter.title,
                "order": chapter.order,
                "status": chapter.status,
                "source_text": chapter.source_text,
                "start_page": chapter.start_page,
                "end_page": chapter.end_page,
                "is_user_edited": chapter.is_user_edited,
                "started_at": chapter.started_at,
                "completed_at": chapter.completed_at,
                "document_id": str(chapter.document.id) if chapter.document else None,
                "modules": modules_list,
                "micro_modules": micro_modules_list,
            })

        return Response(data, status=status.HTTP_200_OK)


class ChapterDetailView(APIView):
    def get(self, request, chapter_id):
        try:
            chapter = Chapter.objects.get(id=chapter_id)
        except (Chapter.DoesNotExist, ValueError):
            chapter = Chapter.objects.order_by("-created_at").first()
            if not chapter:
                return Response(
                    {"error": "Chapter not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        learning_modules = LearningModule.objects.filter(chapter=chapter)
        micro_modules = MicroModule.objects.filter(chapter=chapter)

        modules_data = [
            {
                "id": str(m.id),
                "title": m.title,
                "order": m.order,
                "status": m.status,
                "source_text": m.source_text,
                "start_page": m.start_page,
                "end_page": m.end_page,
                "chapter_id": str(chapter.id),
            }
            for m in learning_modules
        ]

        micro_modules_data = [
            {
                "id": str(mm.id),
                "title": mm.title,
                "order": mm.order,
                "status": mm.status,
                "source_text": mm.source_text,
                "start_page": mm.start_page,
                "end_page": mm.end_page,
                "chapter_id": str(chapter.id),
            }
            for mm in micro_modules
        ]

        target_list = micro_modules_data if micro_modules_data else modules_data
        micro_modules_count = len(target_list)
        completed_count = sum(1 for m in target_list if m["status"] == "completed")
        all_completed = (completed_count == micro_modules_count and micro_modules_count > 0)

        return Response({
            "id": str(chapter.id),
            "document_id": str(chapter.document.id) if chapter.document else None,
            "title": chapter.title,
            "order": chapter.order,
            "source_text": chapter.source_text,
            "start_page": chapter.start_page,
            "end_page": chapter.end_page,
            "is_user_edited": chapter.is_user_edited,
            "status": chapter.status,
            "started_at": chapter.started_at,
            "completed_at": chapter.completed_at,
            "micro_modules_count": micro_modules_count,
            "completed_micro_modules_count": completed_count,
            "all_micro_modules_completed": all_completed,
            "ready_for_assessment": all_completed or chapter.status != Chapter.Status.NOT_STARTED,
            "modules": modules_data,
            "micro_modules": micro_modules_data,
        }, status=status.HTTP_200_OK)


class ChapterStatusUpdateView(APIView):
    def patch(self, request, chapter_id):
        try:
            chapter = Chapter.objects.get(id=chapter_id)
        except (Chapter.DoesNotExist, ValueError):
            chapter = Chapter.objects.order_by("-created_at").first()
            if not chapter:
                return Response(
                    {"error": "Chapter not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        new_status = request.data.get("status")
        if not new_status:
            return Response(
                {"error": "Status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        chapter.status = new_status
        if new_status == Chapter.Status.IN_PROGRESS and not chapter.started_at:
            chapter.started_at = timezone.now()
        elif new_status == Chapter.Status.COMPLETED and not chapter.completed_at:
            chapter.completed_at = timezone.now()

        chapter.save(update_fields=["status", "started_at", "completed_at", "updated_at"])

        return Response({
            "id": str(chapter.id),
            "title": chapter.title,
            "status": chapter.status,
            "started_at": chapter.started_at,
            "completed_at": chapter.completed_at,
        }, status=status.HTTP_200_OK)


class ModuleDetailView(APIView):
    def get(self, request, module_id):
        module = None
        chapter_id = None
        source_text = ""
        status_val = "not_started"
        title = ""

        try:
            lm = LearningModule.objects.get(id=module_id)
            module = lm
            title = lm.title
            source_text = lm.source_text
            status_val = lm.status
            chapter_id = str(lm.chapter.id) if lm.chapter else None
        except (LearningModule.DoesNotExist, ValueError):
            try:
                mm = MicroModule.objects.get(id=module_id)
                module = mm
                title = mm.title
                source_text = mm.source_text
                status_val = mm.status
                chapter_id = str(mm.chapter.id) if mm.chapter else None
            except (MicroModule.DoesNotExist, ValueError):
                # Fallback to latest available module if specified UUID is missing
                mm = MicroModule.objects.order_by("-created_at").first()
                if mm:
                    module = mm
                    title = mm.title
                    source_text = mm.source_text
                    status_val = mm.status
                    chapter_id = str(mm.chapter.id) if mm.chapter else None
                else:
                    return Response(
                        {"error": "Module not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )

        return Response({
            "id": str(module.id),
            "chapter_id": chapter_id,
            "title": title,
            "source_text": source_text,
            "status": status_val,
            "started_at": getattr(module, "started_at", None),
            "completed_at": getattr(module, "completed_at", None),
        }, status=status.HTTP_200_OK)


class MicroModuleListView(APIView):
    def get(self, request):
        modules = MicroModule.objects.all()
        data = [
            {
                "id": str(m.id),
                "chapter_id": str(m.chapter.id) if m.chapter else None,
                "document_id": str(m.document.id) if m.document else None,
                "title": m.title,
                "order": m.order,
                "source_text": m.source_text,
                "start_page": m.start_page,
                "end_page": m.end_page,
                "status": m.status,
                "started_at": m.started_at,
                "completed_at": m.completed_at,
            }
            for m in modules
        ]
        return Response(data, status=status.HTTP_200_OK)


class MicroModuleDetailView(APIView):
    def get(self, request, micro_module_id):
        try:
            m = MicroModule.objects.get(id=micro_module_id)
        except (MicroModule.DoesNotExist, ValueError):
            m = MicroModule.objects.order_by("-created_at").first()
            if not m:
                return Response(
                    {"error": "MicroModule not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        return Response({
            "id": str(m.id),
            "chapter_id": str(m.chapter.id) if m.chapter else None,
            "document_id": str(m.document.id) if m.document else None,
            "title": m.title,
            "order": m.order,
            "source_text": m.source_text,
            "start_page": m.start_page,
            "end_page": m.end_page,
            "status": m.status,
            "started_at": m.started_at,
            "completed_at": m.completed_at,
        }, status=status.HTTP_200_OK)


class MicroModuleStatusUpdateView(APIView):
    def patch(self, request, micro_module_id):
        mm = None
        try:
            mm = MicroModule.objects.get(id=micro_module_id)
        except (MicroModule.DoesNotExist, ValueError):
            try:
                mm = LearningModule.objects.get(id=micro_module_id)
            except (LearningModule.DoesNotExist, ValueError):
                mm = MicroModule.objects.order_by("-created_at").first()
                if not mm:
                    return Response(
                        {"error": "Module not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )

        new_status = request.data.get("status")
        if not new_status:
            return Response(
                {"error": "Status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        mm.status = new_status
        if new_status == "in_progress" and not getattr(mm, "started_at", None):
            mm.started_at = timezone.now()
        elif new_status == "completed" and not getattr(mm, "completed_at", None):
            mm.completed_at = timezone.now()

        mm.save(update_fields=["status", "started_at", "completed_at", "updated_at"])

        return Response({
            "id": str(mm.id),
            "title": mm.title,
            "status": mm.status,
            "started_at": getattr(mm, "started_at", None),
            "completed_at": getattr(mm, "completed_at", None),
        }, status=status.HTTP_200_OK)


class AssessmentGenerateView(APIView):
    def post(self, request):
        data = request.data or {}
        micro_module_id = data.get("micro_module_id")
        micro_module_payload = data.get("micro_module")
        chapter_id = data.get("chapter_id")
        num_mcqs = int(data.get("num_mcqs", 5))
        num_subjective = int(data.get("num_subjective", 2))
        pass_percentage = int(data.get("pass_percentage", 70))

        source_text = ""
        title = ""
        micro_module_obj = None
        chapter_obj = None
        micro_module_id_ref = ""

        if micro_module_id:
            try:
                micro_module_obj = MicroModule.objects.get(id=micro_module_id)
                source_text = micro_module_obj.source_text
                title = micro_module_obj.title
                micro_module_id_ref = str(micro_module_obj.id)
            except (MicroModule.DoesNotExist, ValueError):
                try:
                    lm = LearningModule.objects.get(id=micro_module_id)
                    source_text = lm.source_text
                    title = lm.title
                    micro_module_id_ref = str(lm.id)
                except (LearningModule.DoesNotExist, ValueError):
                    pass

        if not source_text and isinstance(micro_module_payload, dict):
            source_text = micro_module_payload.get("source_text", "")
            title = micro_module_payload.get("title", "Assessment")
            micro_module_id_ref = str(micro_module_payload.get("id", ""))

        if not source_text and chapter_id:
            try:
                chapter_obj = Chapter.objects.get(id=chapter_id)
                source_text = chapter_obj.source_text or "\n\n".join(
                    mm.source_text for mm in chapter_obj.micro_modules.all() if mm.source_text
                )
                title = chapter_obj.title
            except (Chapter.DoesNotExist, ValueError):
                pass

        # Fallback: if user didn't specify micro_module_id/chapter_id or sent empty body in Postman,
        # automatically grab the latest MicroModule or Chapter in SQLite database!
        if not source_text:
            micro_module_obj = MicroModule.objects.order_by("-created_at").first()
            if micro_module_obj:
                source_text = micro_module_obj.source_text
                title = micro_module_obj.title
                micro_module_id_ref = str(micro_module_obj.id)
            else:
                chapter_obj = Chapter.objects.order_by("-created_at").first()
                if chapter_obj:
                    source_text = chapter_obj.source_text
                    title = chapter_obj.title

        if not source_text:
            return Response(
                {"error": "No processed chapters or modules found in database. Please upload and process a document first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract previous questions to avoid duplicates on retest
        previous_questions = []
        prior_assessments = []
        if micro_module_obj:
            prior_assessments = Assessment.objects.filter(micro_module=micro_module_obj)
        elif chapter_obj:
            prior_assessments = Assessment.objects.filter(chapter=chapter_obj)
        elif micro_module_id_ref:
            prior_assessments = Assessment.objects.filter(micro_module_id_ref=micro_module_id_ref)

        for pa in prior_assessments:
            for q in (pa.questions_data or []):
                q_text = q.get("question")
                if q_text:
                    previous_questions.append(q_text)

        questions = generate_assessment_questions(
            source_text=source_text,
            title=title,
            num_mcqs=num_mcqs,
            num_subjective=num_subjective,
            previous_questions=previous_questions
        )

        assessment_type = Assessment.AssessmentType.CHAPTER if chapter_obj else Assessment.AssessmentType.MICRO_MODULE

        assessment = Assessment.objects.create(
            assessment_type=assessment_type,
            chapter=chapter_obj,
            chapter_id_ref=str(chapter_obj.id) if chapter_obj else "",
            micro_module=micro_module_obj if isinstance(micro_module_obj, MicroModule) else None,
            micro_module_id_ref=micro_module_id_ref,
            title=title,
            source_text=source_text,
            questions_data=questions,
            pass_percentage=pass_percentage
        )

        questions_for_student = []
        for q in questions:
            q_type = q.get("type", "mcq")
            item = {
                "id": q.get("id"),
                "type": q_type,
                "question": q.get("question")
            }
            if q_type == "mcq":
                item["options"] = q.get("options", [])
            questions_for_student.append(item)

        return Response({
            "id": str(assessment.id),
            "assessment_type": assessment.assessment_type,
            "chapter": str(chapter_obj.id) if chapter_obj else None,
            "micro_module": str(micro_module_obj.id) if micro_module_obj else None,
            "title": assessment.title,
            "pass_percentage": assessment.pass_percentage,
            "questions_for_student": questions_for_student,
            "created_at": assessment.created_at
        }, status=status.HTTP_201_CREATED)


class AssessmentDetailView(APIView):
    def get(self, request, assessment_id):
        try:
            assessment = Assessment.objects.get(id=assessment_id)
        except (Assessment.DoesNotExist, ValueError):
            assessment = Assessment.objects.order_by("-created_at").first()
            if not assessment:
                return Response(
                    {"error": "Assessment not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        questions = assessment.questions_data or []
        questions_for_student = []
        for q in questions:
            q_type = q.get("type", "mcq")
            item = {
                "id": q.get("id"),
                "type": q_type,
                "question": q.get("question")
            }
            if q_type == "mcq":
                item["options"] = q.get("options", [])
            questions_for_student.append(item)

        return Response({
            "id": str(assessment.id),
            "assessment_type": assessment.assessment_type,
            "chapter": str(assessment.chapter.id) if assessment.chapter else None,
            "micro_module": str(assessment.micro_module.id) if assessment.micro_module else None,
            "title": assessment.title,
            "pass_percentage": assessment.pass_percentage,
            "questions_for_student": questions_for_student,
            "created_at": assessment.created_at
        }, status=status.HTTP_200_OK)


class AssessmentSubmitView(APIView):
    def post(self, request, assessment_id):
        try:
            assessment = Assessment.objects.get(id=assessment_id)
        except (Assessment.DoesNotExist, ValueError):
            assessment = Assessment.objects.order_by("-created_at").first()
            if not assessment:
                return Response(
                    {"error": "Assessment not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        submitted_answers = request.data.get("submitted_answers", {})
        attempt = grade_assessment_attempt(assessment, submitted_answers)

        micro_module_status = None
        if assessment.micro_module:
            micro_module_status = assessment.micro_module.status

        chapter_status = None
        if assessment.chapter:
            chapter_status = assessment.chapter.status

        return Response({
            "id": str(attempt.id),
            "assessment": str(assessment.id),
            "score": attempt.score,
            "total_questions": attempt.total_questions,
            "percentage": attempt.percentage,
            "passed": attempt.passed,
            "detailed_results": attempt.detailed_results,
            "micro_module_status": micro_module_status,
            "chapter_status": chapter_status,
            "created_at": attempt.created_at
        }, status=status.HTTP_200_OK)


class RemediationGenerateView(APIView):
    def post(self, request):
        data = request.data or {}
        assessment_attempt_id = data.get("assessment_attempt_id")
        micro_module_id = data.get("micro_module_id")
        chapter_id = data.get("chapter_id")

        if not assessment_attempt_id and not micro_module_id and not chapter_id:
            # Fallback to latest attempt or latest micro_module
            latest_attempt = AssessmentAttempt.objects.order_by("-created_at").first()
            if latest_attempt:
                assessment_attempt_id = str(latest_attempt.id)
            else:
                latest_mm = MicroModule.objects.order_by("-created_at").first()
                if latest_mm:
                    micro_module_id = str(latest_mm.id)

        try:
            remediation_data = generate_remediation_lesson(
                assessment_attempt_id=assessment_attempt_id,
                micro_module_id=micro_module_id,
                chapter_id=chapter_id
            )
            return Response(remediation_data, status=status.HTTP_200_OK)
        except ValueError as err:
            return Response(
                {"error": str(err)},
                status=status.HTTP_400_BAD_REQUEST
            )