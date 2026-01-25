from django.urls import path
from .views import RecommendationsView

urlpatterns = [
    path("", RecommendationsView.as_view(), name="recommendations"),
]

#from rest_framework.routers import DefaultRouter
#from .views import RecommendationViewSet

#router = DefaultRouter()
#router.register(r"", RecommendationViewSet, basename="recommendations")  # base path

#urlpatterns = router.urls

