from django.contrib import admin
from .models import Chapter, LearningModule, MicroModule, Assessment, AssessmentAttempt

class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0

@admin.register(LearningModule)
class LearningModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "document", "order", "is_user_edited")
    inlines = [ChapterInline]

@admin.register(MicroModule)
class MicroModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "order", "started_at", "completed_at", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "source_text")

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("title", "pass_percentage", "created_at")
    search_fields = ("title",)

@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ("assessment", "score", "total_questions", "percentage", "passed", "created_at")
    list_filter = ("passed",)

