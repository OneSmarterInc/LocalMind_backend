from django.urls import path
from .views import (
    ChapterListView,
    ChapterDetailView,
    ChapterStatusUpdateView,
    ModuleDetailView,
    MicroModuleListView,
    MicroModuleDetailView,
    MicroModuleStatusUpdateView,
    AssessmentGenerateView,
    AssessmentDetailView,
    AssessmentSubmitView,
    RemediationGenerateView,
)

urlpatterns = [
    path("chapters/", ChapterListView.as_view(), name="chapter-list"),
    path("chapters/<uuid:chapter_id>/", ChapterDetailView.as_view(), name="chapter-detail"),
    path("chapters/<uuid:chapter_id>/status/", ChapterStatusUpdateView.as_view(), name="chapter-status-update"),
    path("modules/<uuid:module_id>/", ModuleDetailView.as_view(), name="module-detail"),
    path("micro-modules/", MicroModuleListView.as_view(), name="micro-module-list"),
    path("micro-modules/<uuid:micro_module_id>/", MicroModuleDetailView.as_view(), name="micro-module-detail"),
    path("micro-modules/<uuid:micro_module_id>/status/", MicroModuleStatusUpdateView.as_view(), name="micro-module-status-update"),
    path("assessment/generate/", AssessmentGenerateView.as_view(), name="assessment-generate"),
    path("assessment/<uuid:assessment_id>/", AssessmentDetailView.as_view(), name="assessment-detail"),
    path("assessment/<uuid:assessment_id>/submit/", AssessmentSubmitView.as_view(), name="assessment-submit"),
    path("remediation/generate/", RemediationGenerateView.as_view(), name="remediation-generate"),
]