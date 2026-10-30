"""
The AI model as a swappable part. The agent only calls chat(); changing provider means adding
one function here, nothing else changes.

Uses only the Python standard library (no new packages). The API key is read from the
GEMINI_API_KEY environment variable and sent in a request header, never in the URL or a log.
"""
import json, os, time, urllib.error, urllib.request

DEFAULT_MODEL = "gemini-3.5-flash"   # a pinned version, not a "latest" alias, so runs stay comparable

# The answer must match this shape (structured output), so code can read it without guessing.
FIX_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "reasoning": {"type": "STRING"},
        "wall_thickness_mm": {"type": "ARRAY", "items": {"type": "NUMBER"}},
    },
    "required": ["reasoning", "wall_thickness_mm"],
}


def chat(messages, model=DEFAULT_MODEL, temperature=None):
    """messages: [{"role": "user" | "model", "text": ...}, ...]. Returns (reply_text, meta)."""
    return _gemini(messages, model, temperature)


def _gemini(messages, model, temperature):
    body = {
        "contents": [{"role": m["role"], "parts": [{"text": m["text"]}]} for m in messages],
        "generationConfig": {"responseMimeType": "application/json", "responseSchema": FIX_SCHEMA},
    }
    if temperature is not None:
        body["generationConfig"]["temperature"] = temperature
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]},
    )
    for wait in (15, 30, 60, None):          # free tier: back off when rate-limited or busy (under 2 min in total)
        t0 = time.time()
        try:
            d = json.load(urllib.request.urlopen(req, timeout=120))
            break
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 503) or wait is None:
                raise
            time.sleep(wait)
    text = d["candidates"][0]["content"]["parts"][0]["text"]
    usage = d.get("usageMetadata", {})
    meta = {"provider": "gemini", "model": model, "model_version": d.get("modelVersion"),
            "temperature": temperature, "seconds": round(time.time() - t0, 1),
            "input_tokens": usage.get("promptTokenCount"), "output_tokens": usage.get("candidatesTokenCount")}
    return text, meta
