import json
import requests
from django.conf import settings

def chat(prompt, temperature=0.1):
    response = requests.post(
        f"{settings.OLLAMA_BASE_URL}/api/chat",
        json={
            "model": settings.OLLAMA_CHAT_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": temperature},
        },
        timeout=300,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]

def classify_segment(segment):
    prompt = f"""
You are a neutral bilingual (Hindi and English) public-policy speech classifier.
Classify only issues explicitly discussed in this transcript segment.
Do not infer a politician's intentions, promises, performance, or quality.
Return ONLY valid JSON in this format:
{{
  "issues": [
    {{"category":"Infrastructure","explanation":"short evidence-based reason"}}
  ]
}}
Allowed categories: Infrastructure, Employment, Education, Healthcare, Agriculture,
Water Supply, Electricity, Public Transport, Housing, Environment, Women and Child
Welfare, Law and Order, Social Welfare, Economy, Other.
If no public issue is discussed, return {{"issues":[]}}.
Transcript segment:
{segment}
"""
    raw = chat(prompt)
    try:
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(cleaned)
        return data.get("issues", [])
    except (json.JSONDecodeError, AttributeError):
        return []

def answer_with_context(question, chunks):
    context = "\n\n".join(
        f"[{c['start']:.1f}s - {c['end']:.1f}s] {c['text']}" for c in chunks
    )
    prompt = f"""
Answer the user's question using ONLY the supplied transcript evidence.
The transcript may be Hindi or English. Answer in the language used by the question.
If evidence is insufficient, say so. Do not invent facts or treat campaign claims
as verified facts. Cite timestamps in [mm:ss] format.
Transcript evidence:
{context}

Question: {question}
"""
    return chat(prompt, temperature=0.1)
