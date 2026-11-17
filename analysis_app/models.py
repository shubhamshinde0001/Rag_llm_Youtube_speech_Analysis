from django.db import models

class Politician(models.Model):
    name = models.CharField(max_length=180)
    party = models.CharField(max_length=180, blank=True)
    constituency = models.CharField(max_length=180, blank=True)
    state = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Speech(models.Model):
    STATUS_CHOICES = [
        ("queued", "Queued"), ("processing", "Processing"),
        ("completed", "Completed"), ("failed", "Failed"),
    ]
    politician = models.ForeignKey(Politician, on_delete=models.CASCADE, related_name="speeches")
    title = models.CharField(max_length=250, blank=True)
    youtube_url = models.URLField(max_length=1000)
    video_id = models.CharField(max_length=40, blank=True)
    speech_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=180, blank=True)
    language = models.CharField(max_length=30, blank=True)
    duration_seconds = models.FloatField(default=0)
    audio_file = models.FileField(upload_to="speech_audio/", blank=True)
    transcript_text = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    current_stage = models.CharField(max_length=120, default="Waiting")
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Speech #{self.pk}"

class TranscriptSegment(models.Model):
    speech = models.ForeignKey(Speech, on_delete=models.CASCADE, related_name="segments")
    start_time = models.FloatField()
    end_time = models.FloatField()
    text = models.TextField()
    speaker_label = models.CharField(max_length=80, blank=True)
    class Meta:
        ordering = ["start_time"]

class Ngram(models.Model):
    speech = models.ForeignKey(Speech, on_delete=models.CASCADE, related_name="ngrams")
    phrase = models.CharField(max_length=250)
    n = models.PositiveSmallIntegerField()
    frequency = models.PositiveIntegerField()
    class Meta:
        ordering = ["-frequency"]
        unique_together = ("speech", "phrase", "n")

class IssueMention(models.Model):
    speech = models.ForeignKey(Speech, on_delete=models.CASCADE, related_name="issue_mentions")
    category = models.CharField(max_length=100)
    start_time = models.FloatField(default=0)
    end_time = models.FloatField(default=0)
    segment_text = models.TextField()
    explanation = models.TextField(blank=True)
    word_count = models.PositiveIntegerField(default=0)
    source = models.CharField(max_length=30, default="ollama")
    class Meta:
        ordering = ["start_time"]

class ProcessingLog(models.Model):
    speech = models.ForeignKey(Speech, on_delete=models.CASCADE, related_name="logs")
    stage = models.CharField(max_length=100)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
