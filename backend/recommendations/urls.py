from django.urls import path
from .views import (
    RecommendationsView,
    RecommendationExplainView,
    AgentModelCardView,
    AgentDecisionLogView,
    AgentDecisionStatsView,
)

urlpatterns = [
    # Recommendations
    path("", RecommendationsView.as_view(), name="recommendations"),
    path("<int:pk>/explain/", RecommendationExplainView.as_view(), name="recommendation-explain"),

    # Model Cards
    path("model-cards/", AgentModelCardView.as_view(), name="model-cards-list"),
    path("model-cards/<str:agent_name>/", AgentModelCardView.as_view(), name="model-card-detail"),

    # Decision Logs
    path("decisions/", AgentDecisionLogView.as_view(), name="decision-logs"),
    path("decisions/stats/", AgentDecisionStatsView.as_view(), name="decision-stats"),
]
