import requests
import chromadb
from pathlib import Path
from django.conf import settings

_client = None
_collection = None

def ollama_embed(texts):
    response = requests.post(
        f"{settings.OLLAMA_BASE_URL}/api/embed",
        json={"model": settings.OLLAMA_EMBED_MODEL, "input": texts},
        timeout=180,
    )
    response.raise_for_status()
    return response.json()["embeddings"]

def get_collection():
    global _client, _collection
    if _collection is None:
        path = Path(settings.MEDIA_ROOT) / "chroma_db"
        path.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(path))
        _collection = _client.get_or_create_collection(
            "speech_transcripts",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection

def add_speech_chunks(speech):
    collection = get_collection()
    segments = list(speech.segments.all())
    if not segments:
        return
    docs = [seg.text for seg in segments]
    ids = [f"speech-{speech.id}-segment-{seg.id}" for seg in segments]
    metas = [{
        "speech_id": int(speech.id),
        "start": float(seg.start_time),
        "end": float(seg.end_time),
        "segment_id": int(seg.id),
    } for seg in segments]
    embeddings = ollama_embed(docs)
    collection.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)

def retrieve(question, speech_id, limit=6):
    collection = get_collection()
    query_embedding = ollama_embed([question])[0]
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
        where={"speech_id": int(speech_id)},
    )
    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    return [{
        "text": doc,
        "start": float(meta.get("start", 0)),
        "end": float(meta.get("end", 0)),
    } for doc, meta in zip(docs, metas)]

def ask_speech(question, speech_id):
    from .ollama import answer_with_context
    chunks = retrieve(question, speech_id)
    if not chunks:
        return "I could not find relevant transcript segments for this question.", []
    return answer_with_context(question, chunks), chunks
