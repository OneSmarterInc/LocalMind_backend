from django.urls import path
from .views import TeachMicroModuleView, AskQuestionView, ConversationDetailView

urlpatterns = [
    path(
        "teach/",
        TeachMicroModuleView.as_view(),
        name="teach-micro-module",
    ),
    path(
        "ask/",
        AskQuestionView.as_view(),
        name="ask-question",
    ),
    path(
        "conversations/<uuid:conversation_id>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
]
