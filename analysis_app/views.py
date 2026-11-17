import threading
from collections import defaultdict
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Politician, Speech, Ngram, IssueMention
from .serializers import PoliticianSerializer, SpeechSerializer, SegmentSerializer
from .services.pipeline import process_speech
from .services.rag import ask_speech
from rest_framework.permissions import AllowAny

class PoliticianViewSet(viewsets.ModelViewSet):
    queryset = Politician.objects.all().order_by("name")
    serializer_class = PoliticianSerializer

class SpeechViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Speech.objects.select_related("politician").all().order_by("-created_at")
    serializer_class = SpeechSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        speech = serializer.save()
        # Development MVP only. Use Celery + Redis for production workloads.
        threading.Thread(target=process_speech, args=(speech.id,), daemon=True).start()
        return Response(self.get_serializer(speech).data, status=status.HTTP_201_CREATED)

@api_view(["GET"])
def speech_dashboard(request, speech_id):
    speech = get_object_or_404(Speech, pk=speech_id)
    top = list(speech.ngrams.filter(n=1).order_by("-frequency")[:20].values("phrase", "frequency"))
    bigrams = list(speech.ngrams.filter(n=2).order_by("-frequency")[:15].values("phrase", "frequency"))
    trigrams = list(speech.ngrams.filter(n=3).order_by("-frequency")[:15].values("phrase", "frequency"))
    issue_rows = speech.issue_mentions.values("category").annotate(
        word_count=Sum("word_count"), mentions=Count("id")
    ).order_by("-word_count")
    total_words = sum(x["word_count"] for x in issue_rows) or 0
    issues = [{
        **row,
        "percentage_of_classified_issue_words": round(row["word_count"] / total_words * 100, 2) if total_words else 0
    } for row in issue_rows]
    return Response({
        "speech": SpeechSerializer(speech).data,
        "top_words": top, "bigrams": bigrams, "trigrams": trigrams,
        "issues": issues,
        "segments": SegmentSerializer(speech.segments.all(), many=True).data,
        "total_transcript_words": len((speech.transcript_text or "").split()),
        "issue_mentions_count": speech.issue_mentions.count(),
    })

@api_view(["POST"])
def ask_question(request, speech_id):
    speech = get_object_or_404(Speech, pk=speech_id)
    question = str(request.data.get("question", "")).strip()
    if not question:
        return Response({"error": "Question is required."}, status=400)
    try:
        answer, sources = ask_speech(question, speech.id)
        return Response({"answer": answer, "sources": sources})
    except Exception as exc:
        return Response({"error": f"RAG/Ollama error: {exc}"}, status=503)

@api_view(["GET"])
def health(request):
    return Response({"status": "ok", "application": "Political Speech Intelligence"})
