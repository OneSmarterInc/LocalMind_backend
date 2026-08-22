from rest_framework import serializers

from .models import Assessment, AssessmentAttempt, Chapter, LearningModule, MicroModule


class LearningModuleSerializer(serializers.ModelSerializer):
    chapter_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = LearningModule
        fields = [
            "id",
            "title",
            "order",
            "chapter_id",
            "source_text",
            "start_page",
            "end_page",
            "is_user_edited",
            "status",
            "started_at",
            "completed_at",
        ]


class ChapterSerializer(serializers.ModelSerializer):
    document_id = serializers.UUIDField(read_only=True)
    modules = LearningModuleSerializer(many=True, read_only=True)

    class Meta:
        model = Chapter
        fields = [
            "id",
            "document_id",
            "title",
            "order",
            "source_text",
            "start_page",
            "end_page",
            "is_user_edited",
            "status",
            "started_at",
            "completed_at",
            "modules",
        ]


# Lightweight serializers used by the document structure API
class LearningModuleStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningModule
        fields = [
            "id",
            "title",
            "order",
        ]


class ChapterStructureSerializer(serializers.ModelSerializer):
    modules = LearningModuleStructureSerializer(many=True, read_only=True)

    class Meta:
        model = Chapter
        fields = [
            "id",
            "title",
            "order",
            "modules",
        ]


class MicroModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MicroModule
        fields = [
            "id",
            "document",
            "chapter",
            "title",
            "order",
            "source_text",
            "start_page",
            "end_page",
            "is_user_edited",
            "status",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]


class AssessmentQuestionStudentSerializer(serializers.Serializer):
    """
    Hides correct answers and explanations when serving question paper to student.
    """
    id = serializers.CharField()
    type = serializers.CharField(default="mcq")
    question = serializers.CharField()
    options = serializers.ListField(child=serializers.DictField(), required=False)


class AssessmentSerializer(serializers.ModelSerializer):
    questions_for_student = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = [
            "id",
            "assessment_type",
            "chapter",
            "micro_module",
            "micro_module_id_ref",
            "title",
            "pass_percentage",
            "questions_data",
            "questions_for_student",
            "created_at",
        ]

    def get_questions_for_student(self, obj):
        questions = obj.questions_data or []
        student_questions = []
        for q in questions:
            q_type = q.get("type", "mcq")
            item = {
                "id": q.get("id"),
                "type": q_type,
                "question": q.get("question"),
            }
            if q_type == "mcq":
                item["options"] = q.get("options", [])
            student_questions.append(item)
        return student_questions


class AssessmentAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentAttempt
        fields = [
            "id",
            "assessment",
            "submitted_answers",
            "score",
            "total_questions",
            "percentage",
            "passed",
            "detailed_results",
            "created_at",
        ]
