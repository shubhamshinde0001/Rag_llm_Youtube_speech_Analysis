from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PoliticianViewSet, SpeechViewSet, speech_dashboard, ask_question, health

router = DefaultRouter()
router.register("politicians", PoliticianViewSet)
router.register("speeches", SpeechViewSet)

urlpatterns = [
    path("health/", health),
    path("dashboard/<int:speech_id>/", speech_dashboard),
    path("speeches/<int:speech_id>/ask/", ask_question),
    path("", include(router.urls)),
]
