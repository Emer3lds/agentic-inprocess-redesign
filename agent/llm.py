"""
The AI model as a swappable part. The agents only call chat() (v0) and step() (v1); which provider
answers is decided by the model name, so nothing else changes when the provider changes.

  "openrouter:<model id>"  -> OpenRouter (key in OPENROUTER_API_KEY), e.g. openrouter:google/gemini-3.6-flash
  any other name           -> Google's Gemini API directly (key in GEMINI_API_KEY), e.g. gemini-3.5-flash

Uses only the Python standard library (no new packages). Keys are read from environment variables and
sent in a request header, never in the URL or a log.
"""
import json, os, time, urllib.error, urllib.request

# Pinned model ids, not "latest" aliases, so runs stay comparable. Every call also logs the version
# the provider reports back. Main model: free Nemotron 3 Ultra (D11).
DEFAULT_MODEL = "openrouter:nvidia/nemotron-3-ultra-550b-a55b:free"
OPENROUTER = "openrouter:"

# The answer must match this shape (structured output), so code can read it without guessing.
FIX_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "reasoning": {"type": "STRING"},
        "wall_thickness_mm": {"type": "ARRAY", "items": {"type": "NUMBER"}},
    },
    "required": ["reasoning", "wall_thickness_mm"],
}


def step(contents, tools, model=DEFAULT_MODEL):
    """One turn of a tool-using conversation (agent v1). contents: the conversation so far in Gemini's
    format; tools: function declarations. Returns (the model's content, meta). The model's content must
    be appended to contents unchanged, since the provider expects its own reply (incl. hidden reasoning
    signatures) back."""
    if model.startswith(OPENROUTER):
        return _openrouter_step(contents, tools, model)
    body = {"contents": contents, "tools": [{"functionDeclarations": tools}]}
    d, seconds = _post_gemini(model, body)
    usage = d.get("usageMetadata", {})
    content = d["candidates"][0].get("content", {"role": "model", "parts": []})
    content.setdefault("role", "model"); content.setdefault("parts", [])
    return content, {"provider": "gemini", "model": model, "model_version": d.get("modelVersion"),
                     "seconds": seconds, "input_tokens": usage.get("promptTokenCount"),
                     "output_tokens": usage.get("candidatesTokenCount")}


def chat(messages, model=DEFAULT_MODEL, temperature=None):
    """messages: [{"role": "user" | "model", "text": ...}, ...]. Returns (reply_text, meta)."""
    if model.startswith(OPENROUTER):
        return _openrouter_chat(messages, model, temperature)
    return _gemini(messages, model, temperature)


# ---------- retries shared by both providers ----------

TIMEOUT = int(os.environ.get("LLM_TIMEOUT_S", 180))   # seconds one call may take before giving up
RETRY_WAITS = () if os.environ.get("LLM_NO_RETRY") else (15, 30, 60)


def _with_retries(send):
    for wait in (*RETRY_WAITS, None):        # back off when rate-limited or busy (under 2 min in total)
        t0 = time.time()
        try:
            return send(), round(time.time() - t0, 1)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503) or wait is None:
                raise
            time.sleep(wait)


# ---------- Google Gemini API ----------

def _post_gemini(model, body):
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]},
    )
    return _with_retries(lambda: json.load(urllib.request.urlopen(req, timeout=120)))


def _gemini(messages, model, temperature):
    body = {
        "contents": [{"role": m["role"], "parts": [{"text": m["text"]}]} for m in messages],
        "generationConfig": {"responseMimeType": "application/json", "responseSchema": FIX_SCHEMA},
    }
    if temperature is not None:
        body["generationConfig"]["temperature"] = temperature
    d, seconds = _post_gemini(model, body)
    text = d["candidates"][0]["content"]["parts"][0]["text"]
    usage = d.get("usageMetadata", {})
    meta = {"provider": "gemini", "model": model, "model_version": d.get("modelVersion"),
            "temperature": temperature, "seconds": seconds,
            "input_tokens": usage.get("promptTokenCount"), "output_tokens": usage.get("candidatesTokenCount")}
    return text, meta


# ---------- OpenRouter (OpenAI-style messages) ----------

def _post_openrouter(body):
    url = "https://openrouter.ai/api/v1/chat/completions"
    req = urllib.request.Request(url, data=json.dumps({**body, "usage": {"include": True}}).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]})

    def send():
        d = json.load(urllib.request.urlopen(req, timeout=TIMEOUT))
        if "error" in d:                      # OpenRouter can report a provider error inside a 200 reply
            code = d["error"].get("code")
            raise urllib.error.HTTPError(url, code if isinstance(code, int) else 502, str(d["error"].get("message")), None, None)
        return d
    return _with_retries(send)


def _openrouter_meta(d, model, seconds, temperature=None):
    u = d.get("usage", {})
    return {"provider": "openrouter", "model": model, "model_version": d.get("model"),
            "served_by": d.get("provider"), "temperature": temperature, "seconds": seconds,
            "input_tokens": u.get("prompt_tokens"), "output_tokens": u.get("completion_tokens"),
            "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
            "cost_usd": u.get("cost")}


def _json_schema(s):
    """Gemini writes schema types in capitals (OBJECT); OpenAI-style JSON schema needs lower case."""
    if all(isinstance(v, dict) for v in s.values()) and "type" not in s:   # a "properties" map: name -> schema
        return {k: _json_schema(v) for k, v in s.items()}
    out = {k: (v.lower() if k == "type" else _json_schema(v) if isinstance(v, dict) else v) for k, v in s.items()}
    if out.get("type") == "object":
        out["additionalProperties"] = False
    return out


_structured_models = None


def _supports_structured_output(model_id):
    """Asks OpenRouter once which models can be forced to answer in a fixed JSON format."""
    global _structured_models
    if _structured_models is None:
        models = json.load(urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=60))["data"]
        _structured_models = {m["id"] for m in models if "structured_outputs" in m.get("supported_parameters", [])}
    return model_id in _structured_models


def _openrouter_chat(messages, model, temperature):
    model_id = model[len(OPENROUTER):]
    body = {"model": model_id,
            "messages": [{"role": "assistant" if m["role"] == "model" else "user", "content": m["text"]} for m in messages]}
    if _supports_structured_output(model_id):   # otherwise rely on the prompt's "Only JSON"; parse() and the checker catch bad replies
        body["response_format"] = {"type": "json_schema", "json_schema": {"name": "fix", "strict": True, "schema": _json_schema(FIX_SCHEMA)}}
    if temperature is not None:
        body["temperature"] = temperature
    d, seconds = _post_openrouter(body)
    return d["choices"][0]["message"]["content"], _openrouter_meta(d, model, seconds, temperature)


def _to_openai_messages(contents):
    """Translate the agent's Gemini-format conversation into OpenAI-style messages."""
    msgs, last_calls = [], []
    for c in contents:
        if c["role"] == "model":
            msgs.append(c["_openrouter_message"])          # the provider's own reply, sent back unchanged
            last_calls = c["_openrouter_message"].get("tool_calls") or []
            continue
        for i, p in enumerate(x for x in c["parts"] if "functionResponse" in x):
            msgs.append({"role": "tool", "tool_call_id": last_calls[i]["id"],
                         "content": json.dumps(p["functionResponse"]["response"])})
        text = " ".join(p["text"] for p in c["parts"] if "text" in p)
        if text:
            msgs.append({"role": "user", "content": text})
    return msgs


def _openrouter_step(contents, tools, model):
    body = {"model": model[len(OPENROUTER):], "messages": _to_openai_messages(contents),
            "tools": [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                                        "parameters": _json_schema(t["parameters"])}} for t in tools]}
    d, seconds = _post_openrouter(body)
    m = d["choices"][0]["message"]
    parts = [{"text": m["content"]}] if m.get("content") else []
    for tc in m.get("tool_calls") or []:
        try:
            args = json.loads(tc["function"].get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {"_unreadable_arguments": tc["function"].get("arguments")}
        parts.append({"functionCall": {"name": tc["function"]["name"], "args": args, "id": tc["id"]}})
    return {"role": "model", "parts": parts, "_openrouter_message": m}, _openrouter_meta(d, model, seconds)
