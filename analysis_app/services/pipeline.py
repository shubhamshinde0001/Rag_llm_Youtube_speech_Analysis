from pathlib import Path
from django.core.files import File
from django.db import close_old_connections
from ..models import Speech, TranscriptSegment, Ngram, IssueMention, ProcessingLog
from .youtube import download_audio, extract_video_id
from .transcription import transcribe_audio
from .nlp import calculate_ngrams, count_words
from .ollama import classify_segment
from .rag import add_speech_chunks

def log(speech, stage, message=""):
    ProcessingLog.objects.create(speech=speech, stage=stage, message=message)
    speech.current_stage = stage
    speech.save(update_fields=["current_stage"])

def process_speech(speech_id):
    close_old_connections()
    speech = Speech.objects.get(pk=speech_id)
    try:
        speech.status = "processing"
        speech.error_message = ""
        speech.save(update_fields=["status", "error_message"])
        log(speech, "Extracting audio")
        audio_path, duration, title = download_audio(speech.youtube_url, speech.id)
        speech.video_id = extract_video_id(speech.youtube_url)
        speech.duration_seconds = duration
        if not speech.title:
            speech.title = title
        with open(audio_path, "rb") as f:
            speech.audio_file.save(audio_path.name, File(f), save=False)
        speech.save()

        log(speech, "Transcribing Hindi / English audio")
        segments, language, detected_duration = transcribe_audio(audio_path)
        speech.language = language
        speech.duration_seconds = detected_duration or duration
        speech.transcript_text = "\n".join(x["text"] for x in segments)
        speech.save()

        log(speech, "Saving timestamped transcript")
        speech.segments.all().delete()
        TranscriptSegment.objects.bulk_create([
            TranscriptSegment(
                speech=speech, start_time=x["start"], end_time=x["end"], text=x["text"]
            ) for x in segments
        ])

        log(speech, "Calculating word and phrase frequencies")
        speech.ngrams.all().delete()
        Ngram.objects.bulk_create([
            Ngram(speech=speech, phrase=phrase, n=n, frequency=count)
            for phrase, n, count in calculate_ngrams(speech.transcript_text)
        ])

        log(speech, "Classifying public issues with Ollama")
        speech.issue_mentions.all().delete()
        mentions = []
        for seg in segments:
            try:
                issues = classify_segment(seg["text"])
            except Exception as exc:
                log(speech, "Ollama issue classification warning", str(exc))
                issues = []
            for issue in issues:
                category = str(issue.get("category", "Other"))[:100]
                mentions.append(IssueMention(
                    speech=speech, category=category,
                    start_time=seg["start"], end_time=seg["end"],
                    segment_text=seg["text"],
                    explanation=str(issue.get("explanation", "")),
                    word_count=count_words(seg["text"]), source="ollama"
                ))
        IssueMention.objects.bulk_create(mentions)

        log(speech, "Indexing transcript for RAG")
        add_speech_chunks(speech)
        speech.status = "completed"
        speech.current_stage = "Completed"
        speech.save(update_fields=["status", "current_stage"])
        log(speech, "Completed", "Speech processing completed successfully.")
    except Exception as exc:
        speech.status = "failed"
        speech.error_message = str(exc)
        speech.current_stage = "Failed"
        speech.save(update_fields=["status", "error_message", "current_stage"])
        log(speech, "Failed", str(exc))
    finally:
        close_old_connections()
