"""Cloud helper for Quantum Mind.

Default provider is Groq (keys usually start with gsk_).
Gemini keys still work if you paste one later.
Do not share your key.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import urllib.error
import urllib.request

from database import load_settings, save_settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS = (
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-20b",
)
GROQ_VISION_MODELS = (
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
)
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_MODELS = ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite")

SYSTEM = (
    "You are Quantum Mind, a general assistant for everyone. "
    "You were created by Emmanuel Abraham. Your on-screen face is a holographic "
    "assistant inspired by Gideon from The Flash, but your name is Quantum Mind. "
    "Speak as a clear, helpful guide. Keep answers family-friendly. "
    "Do not give adult, violent, or dangerous how-to content. "
    "Do not help with hacking or breaking into accounts, phones, or systems. "
    "Do not claim you can clone a real person's voice or control a whole phone. "
    "If you are unsure, say so briefly. Prefer short spoken-style answers unless "
    "the person asks for more detail."
)


def get_api_key() -> str:
    settings = load_settings()
    return str(settings.get("api_key") or settings.get("gemini_api_key") or "").strip()


def save_api_key(key: str) -> None:
    settings = load_settings()
    settings["api_key"] = key.strip()
    save_settings(settings)


def has_api_key() -> bool:
    return bool(get_api_key())


def provider_for_key(key: str) -> str:
    low = key.lower()
    if low.startswith("gsk_"):
        return "groq"
    if low.startswith("aiza") or "gemini" in low:
        return "gemini"
    return "groq"


def key_status() -> str:
    key = get_api_key()
    if not key:
        return "Cloud brain is off. Add a Groq API key."
    tail = key[-4:] if len(key) >= 4 else "****"
    return f"Cloud brain is on ({provider_for_key(key)}). Key ending {tail}."


def _http_json(url: str, payload: dict, headers: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _history_to_groq_messages(history):
    messages = []
    for turn in history or []:
        if turn.get("q"):
            messages.append({"role": "user", "content": turn["q"]})
        if turn.get("a"):
            messages.append({"role": "assistant", "content": turn["a"]})
    return messages


def _ask_groq(key: str, prompt: str, history=None) -> str:
    last_error = None
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + key,
    }
    for model in GROQ_MODELS:
        payload = {
            "model": model,
            "temperature": 0.6,
            "max_tokens": 512,
            "messages": (
                [{"role": "system", "content": SYSTEM}]
                + _history_to_groq_messages(history)
                + [{"role": "user", "content": prompt}]
            ),
        }
        try:
            body = _http_json(GROQ_URL, payload, headers)
            text = body["choices"][0]["message"]["content"].strip()
            if text:
                return text
        except urllib.error.HTTPError as exc:
            last_error = exc
            detail = exc.read().decode("utf-8", errors="ignore")[:180]
            if exc.code in (400, 404):
                continue
            raise RuntimeError(f"Groq error {exc.code}: {detail}") from exc
        except Exception as exc:
            last_error = exc
            continue
    raise RuntimeError(f"Groq request failed. Check the API key. ({last_error})")


def _history_to_gemini_contents(history):
    contents = []
    for turn in history or []:
        if turn.get("q"):
            contents.append({"role": "user", "parts": [{"text": turn["q"]}]})
        if turn.get("a"):
            contents.append({"role": "model", "parts": [{"text": turn["a"]}]})
    return contents


def _ask_gemini(key: str, prompt: str, history=None) -> str:
    last_error = None
    for model in GEMINI_MODELS:
        url = GEMINI_URL.format(model=model)
        payload = {
            "systemInstruction": {"parts": [{"text": SYSTEM}]},
            "contents": _history_to_gemini_contents(history) + [
                {"role": "user", "parts": [{"text": prompt}]}
            ],
            "generationConfig": {"temperature": 0.6, "maxOutputTokens": 512},
        }
        headers = {"Content-Type": "application/json", "x-goog-api-key": key}
        try:
            body = _http_json(url, payload, headers)
            parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            text = "".join(part.get("text", "") for part in parts).strip()
            if text:
                return text
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in (400, 403, 404):
                continue
            detail = exc.read().decode("utf-8", errors="ignore")[:180]
            raise RuntimeError(f"Gemini error {exc.code}: {detail}") from exc
        except Exception as exc:
            last_error = exc
            continue
    raise RuntimeError(f"Gemini request failed. Check the API key. ({last_error})")


def ask_cloud(
    question: str,
    username: str = "student",
    context: str | None = None,
    history: list | None = None,
) -> str:
    key = get_api_key()
    if not key:
        raise RuntimeError("No API key saved")
    if context:
        prompt = (
            f"Student username: {username}\n"
            f"Here is text from a document the student loaded (it may be truncated):\n"
            f"---\n{context}\n---\n"
            f"Using that document, answer this question: {question}"
        )
    else:
        prompt = f"Student username: {username}\nQuestion: {question}"
    if provider_for_key(key) == "gemini":
        return _ask_gemini(key, prompt, history=history)
    return _ask_groq(key, prompt, history=history)


def _image_to_data(image_path: str) -> tuple[str, str]:
    mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return mime_type, b64


def _ask_groq_vision(key: str, prompt: str, image_path: str) -> str:
    mime_type, b64 = _image_to_data(image_path)
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + key}
    last_error = None
    for model in GROQ_VISION_MODELS:
        payload = {
            "model": model,
            "temperature": 0.5,
            "max_tokens": 512,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
                    ],
                },
            ],
        }
        try:
            body = _http_json(GROQ_URL, payload, headers)
            text = body["choices"][0]["message"]["content"].strip()
            if text:
                return text
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in (400, 404):
                continue
            detail = exc.read().decode("utf-8", errors="ignore")[:180]
            raise RuntimeError(f"Groq error {exc.code}: {detail}") from exc
        except Exception as exc:
            last_error = exc
            continue
    raise RuntimeError(f"Groq vision request failed. ({last_error})")


def _ask_gemini_vision(key: str, prompt: str, image_path: str) -> str:
    mime_type, b64 = _image_to_data(image_path)
    last_error = None
    for model in GEMINI_MODELS:
        url = GEMINI_URL.format(model=model)
        payload = {
            "systemInstruction": {"parts": [{"text": SYSTEM}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {"inlineData": {"mimeType": mime_type, "data": b64}},
                    ],
                }
            ],
            "generationConfig": {"temperature": 0.5, "maxOutputTokens": 512},
        }
        headers = {"Content-Type": "application/json", "x-goog-api-key": key}
        try:
            body = _http_json(url, payload, headers)
            parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            text = "".join(part.get("text", "") for part in parts).strip()
            if text:
                return text
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in (400, 403, 404):
                continue
            detail = exc.read().decode("utf-8", errors="ignore")[:180]
            raise RuntimeError(f"Gemini error {exc.code}: {detail}") from exc
        except Exception as exc:
            last_error = exc
            continue
    raise RuntimeError(f"Gemini vision request failed. ({last_error})")


def ask_cloud_about_image(question: str, image_path: str, username: str = "student") -> str:
    key = get_api_key()
    if not key:
        raise RuntimeError("No API key saved")
    prompt = f"Student username: {username}\nQuestion about the attached picture: {question}"
    if provider_for_key(key) == "gemini":
        return _ask_gemini_vision(key, prompt, image_path)
    return _ask_groq_vision(key, prompt, image_path)


# Older Brain.py imports
ask_gemini = ask_cloud
