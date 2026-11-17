
import re
from pathlib import Path
import yt_dlp
from django.conf import settings


def extract_video_id(url):
    patterns = [
        r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return ""


def download_audio(url, speech_id):

    output_dir = Path(settings.MEDIA_ROOT) / "speech_audio"
    output_dir.mkdir(parents=True, exist_ok=True)

    template = str(output_dir / f"speech_{speech_id}.%(ext)s")

    options = {
        "format": "bestaudio/best",
        "outtmpl": template,
        "noplaylist": True,
        "quiet": True,

        # Explicit FFmpeg location
        "ffmpeg_location": r"C:\ffmpeg\bin",

        # Explicit Deno JavaScript runtime
        "js_runtimes": {
            "deno": {
                "path": r"C:\Users\Shubham\.deno\bin\deno.exe"
            }
        },

        # Convert downloaded audio into WAV
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)

        wav_path = output_dir / f"speech_{speech_id}.wav"

        if not wav_path.exists():

            candidates = list(output_dir.glob(f"speech_{speech_id}.*"))

            if not candidates:
                raise RuntimeError(
                    "Audio file was not created. Check FFmpeg installation."
                )

            raise RuntimeError(
                f"Expected WAV file was not created. Found: {candidates}"
            )

        duration = float(info.get("duration") or 0)

        if duration > settings.MAX_VIDEO_MINUTES * 60:

            wav_path.unlink(missing_ok=True)

            raise ValueError(
                f"Video exceeds the configured "
                f"{settings.MAX_VIDEO_MINUTES}-minute limit."
            )

        return wav_path, duration, info.get("title", "")

    except Exception:
        raise
