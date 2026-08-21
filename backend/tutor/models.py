import uuid
from django.db import models


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    micro_module_id = models.CharField(max_length=128, db_index=True)
    micro_module_title = models.CharField(max_length=300, blank=True)
    source_text = models.TextField(blank=True)
    start_page = models.IntegerField(null=True, blank=True)
    end_page = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Conversation {self.id} ({self.micro_module_title or self.micro_module_id})"


class Message(models.Model):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        TUTOR = "tutor", "Tutor"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    answer_status = models.CharField(max_length=30, blank=True)
    key_points = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.role}] {self.content[:40]}..."
