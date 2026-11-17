from faster_whisper import WhisperModel
from django.conf import settings

_model = None

def get_model():
    global _model
    if _model is None:
        _model = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
        )
    return _model

def transcribe_audio(audio_path):
    model = get_model()
    segments, info = model.transcribe(
        str(audio_path),
        language=None,             # auto-detect Hindi or English
        task="transcribe",
        beam_size=5,
        vad_filter=True,
        word_timestamps=False,
    )
    output = []
    for segment in segments:
        text = (segment.text or "").strip()
        if text:
            output.append({
                "start": float(segment.start),
                "end": float(segment.end),
                "text": text,
            })
    return output, (info.language or "unknown"), float(info.duration or 0)
