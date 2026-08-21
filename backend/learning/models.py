import uuid
from django.db import models

class LearningModule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="modules",
    )
    title = models.CharField(max_length=300)
    order = models.PositiveIntegerField()
    is_user_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "order"],
                name="unique_module_order_per_document",
            )
        ]

    def __str__(self):
        return self.title

class Chapter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(
        LearningModule,
        on_delete=models.CASCADE,
        related_name="chapters",
    )
    title = models.CharField(max_length=300)
    order = models.PositiveIntegerField()
    is_user_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["module", "order"],
                name="unique_chapter_order_per_module",
            )
        ]

    def __str__(self):
        return self.title


class MicroModule(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        NEEDS_REVIEW = "needs_review", "Needs Review"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="micro_modules",
    )
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="micro_modules",
    )
    title = models.CharField(max_length=300)
    order = models.PositiveIntegerField(default=1)
    source_text = models.TextField()
    start_page = models.IntegerField(null=True, blank=True)
    end_page = models.IntegerField(null=True, blank=True)
    is_user_edited = models.BooleanField(default=False)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.NOT_STARTED,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class Assessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    micro_module = models.ForeignKey(
        MicroModule,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assessments",
    )
    micro_module_id_ref = models.CharField(max_length=128, blank=True)
    title = models.CharField(max_length=300)
    source_text = models.TextField(blank=True)
    questions_data = models.JSONField(default=list)
    pass_percentage = models.IntegerField(default=70)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Assessment for {self.title}"


class AssessmentAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    submitted_answers = models.JSONField(default=dict)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    percentage = models.FloatField()
    passed = models.BooleanField(default=False)
    detailed_results = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Attempt on {self.assessment.title} - Score: {self.score}/{self.total_questions} ({self.percentage}%)"

