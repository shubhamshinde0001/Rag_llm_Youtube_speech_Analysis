# Political Speech Intelligence (Hindi + English)

A local-first Django MVP for analyzing public political speeches. It extracts audio from a permitted YouTube video, transcribes Hindi/English speech with Faster-Whisper, calculates unigrams/bigrams/trigrams, classifies public-issue excerpts with Ollama, stores transcript segments, and provides a basic RAG question-answering interface.

## 1. Requirements

- Python 3.10 or 3.11 recommended
- FFmpeg installed and available on PATH
- Ollama installed and running
- Enough RAM/disk for the selected Whisper model
- Internet access to download public video audio and model files

This application is for research and civic information. Only process material you have the right to access and process. Respect YouTube terms, copyright, privacy and applicable law. Do not present automated speaker attribution or issue classification as verified fact.

## 2. Install Ollama models

Open a terminal:

```bash
ollama pull llama3.2:latest
ollama pull nomic-embed-text:latest
ollama serve
```

The application uses the Ollama chat model for issue classification and answers, and calls Ollama's `/api/embed` endpoint with `nomic-embed-text` for ChromaDB document and query embeddings.

Check Ollama:
```bash
ollama list
```

## 3. Install FFmpeg

Windows: install FFmpeg and add its `bin` directory to PATH.
Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ffmpeg
```
Verify:
```bash
ffmpeg -version
```

## 4. Set up Django

Windows PowerShell:
```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Linux/macOS:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:
- Dashboard: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Health: http://127.0.0.1:8000/api/health/

## 5. Add a politician

Log in to Django Admin and create a Politician record. Add the name, party and state. Then return to the dashboard and submit a public YouTube URL.

The processing stages are:
1. Extract audio with yt-dlp and FFmpeg.
2. Transcribe with Faster-Whisper (language auto-detection).
3. Save timestamped transcript segments.
4. Calculate top 100 unigrams, bigrams and trigrams.
5. Ask Ollama to classify each transcript segment into public-issue categories.
6. Index segments in local ChromaDB for retrieval.
7. Ask questions about the selected speech.

## 6. Hindi + English behavior

Faster-Whisper auto-detects the speech language. The tokenizer handles Latin and Devanagari script. The included stop-word list is intentionally small and should be expanded and reviewed against your dataset. For code-mixed Hindi-English (Hinglish), expect some tokenization and spelling variation. Add language-specific normalization and curated stop-word lists before treating counts as research-grade statistics.

## 7. API endpoints

- `GET/POST /api/politicians/`
- `GET/POST /api/speeches/`
- `GET /api/dashboard/<speech_id>/`
- `POST /api/speeches/<speech_id>/ask/`
- `GET /api/health/`

Example question request:
```json
{"question":"What did the speaker say about employment?"}
```

## 8. Important MVP limitations

- The processing thread is a development convenience. It is not durable: if Django stops, a job can stop. For deployment, replace it with Celery + Redis and add retries, job locking and progress tracking.
- This first version does not identify or verify a politician's voice. Voice verification and speaker diarization are separate modules and should only be added with appropriate reference recordings, consent/legal review, confidence thresholds and human review.
- The first issue chart counts classified segment mentions. The reported percentage is the share of words in classified issue segments, not a measure of policy priority, sincerity or actual governance performance.
- RAG embeddings are generated locally through Ollama's `nomic-embed-text` model and stored in persistent ChromaDB.
- Do not expose this development server publicly. Add authentication, authorization, upload limits, rate limits, audit logs and secure storage before deployment.
- Validate model output and transcript excerpts. ASR can mishear names, places, numbers, and code-mixed speech.

## 9. PostgreSQL

Set `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` in `.env`. If `DB_NAME` is blank, the project uses SQLite for local setup. Run migrations after changing the database.

## 10. Troubleshooting

- `ffmpeg not found`: install FFmpeg and restart the terminal.
- Ollama connection refused: run `ollama serve` and check `OLLAMA_BASE_URL`.
- Model not found: run `ollama pull llama3.2:latest`.
- Whisper download/slow first run: first launch downloads the configured model. Change `WHISPER_MODEL` in `.env` to `tiny` for a quick smoke test or `small` for better accuracy.
- CUDA errors: keep `WHISPER_DEVICE=cpu` and `WHISPER_COMPUTE_TYPE=int8`.
- YouTube download fails: the video may be private, age-restricted, region-restricted, unavailable, or unsupported. Use only content you are permitted to process.
