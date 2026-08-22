from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("id", "role", "content", "answer_status", "key_points", "created_at")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "micro_module_id", "micro_module_title", "created_at", "updated_at")
    search_fields = ("id", "micro_module_id", "micro_module_title")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "role", "answer_status", "created_at")
    list_filter = ("role", "answer_status")
    search_fields = ("content",)
