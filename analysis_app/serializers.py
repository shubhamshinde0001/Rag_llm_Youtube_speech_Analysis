from rest_framework import serializers
from .models import Politician, Speech, TranscriptSegment, Ngram, IssueMention

class PoliticianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Politician
        fields = "__all__"

class SpeechSerializer(serializers.ModelSerializer):
    politician_name = serializers.CharField(source="politician.name", read_only=True)
    class Meta:
        model = Speech
        fields = "__all__"
        read_only_fields = ["status", "current_stage", "error_message", "transcript_text",
                            "duration_seconds", "language", "video_id", "audio_file"]

class SegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscriptSegment
        fields = "__all__"

class NgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ngram
        fields = "__all__"

class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueMention
        fields = "__all__"
