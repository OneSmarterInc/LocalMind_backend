from django.urls import path
from .views import (
    AssessmentDetailView,
    AssessmentGenerateView,
    AssessmentSubmitView,
    MicroModuleDetailView,
    MicroModuleListCreateView,
    RemediationGenerateView,
)

urlpatterns = [
    path(
        "micro-modules/",
        MicroModuleListCreateView.as_view(),
        name="micro-module-list-create",
    ),
    path(
        "micro-modules/<uuid:micro_module_id>/",
        MicroModuleDetailView.as_view(),
        name="micro-module-detail",
    ),
    path(
        "micro-modules/<uuid:micro_module_id>/status/",
        MicroModuleDetailView.as_view(),
        name="micro-module-status-update",
    ),
    path(
        "assessment/generate/",
        AssessmentGenerateView.as_view(),
        name="assessment-generate",
    ),
    path(
        "assessment/<uuid:assessment_id>/",
        AssessmentDetailView.as_view(),
        name="assessment-detail",
    ),
    path(
        "assessment/<uuid:assessment_id>/submit/",
        AssessmentSubmitView.as_view(),
        name="assessment-submit",
    ),
    path(
        "remediation/generate/",
        RemediationGenerateView.as_view(),
        name="remediation-generate",
    ),
]

