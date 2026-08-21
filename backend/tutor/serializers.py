from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "role",
            "content",
            "answer_status",
            "key_points",
            "created_at",
        ]


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "micro_module_id",
            "micro_module_title",
            "start_page",
            "end_page",
            "created_at",
            "updated_at",
            "messages",
        ]
