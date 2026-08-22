from django.contrib import admin
from .models import Assessment, AssessmentAttempt, Chapter, LearningModule, MicroModule


class LearningModuleInline(admin.TabularInline):
    model = LearningModule
    extra = 0


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("title", "document", "order", "status", "start_page", "end_page")
    list_filter = ("status",)
    search_fields = ("title", "source_text")
    inlines = [LearningModuleInline]


@admin.register(LearningModule)
class LearningModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "chapter", "order", "status", "start_page", "end_page")
    list_filter = ("status",)
    search_fields = ("title", "source_text")


@admin.register(MicroModule)
class MicroModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "order", "started_at", "completed_at", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "source_text")


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("title", "assessment_type", "pass_percentage", "created_at")
    list_filter = ("assessment_type",)
    search_fields = ("title",)


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ("assessment", "score", "total_questions", "percentage", "passed", "created_at")
    list_filter = ("passed",)
