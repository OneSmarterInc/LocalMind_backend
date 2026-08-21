from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("original_name", "status", "file_type", "created_at")
    list_filter = ("status", "file_type")
    search_fields = ("original_name", "title")
