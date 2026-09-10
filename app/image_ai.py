"""Image generation and editing for Quantum Mind.

Uses OpenAI's Images API (https://platform.openai.com/docs/guides/images)
with a key the user supplies themselves, the same "bring your own key"
pattern used for the Cloud (Groq/Gemini) and Avatar (D-ID) features.

Two things this module can do:
  generate_image(prompt)             -> brand new picture from a text prompt
  edit_image(source_path, prompt)    -> change an existing picture using a
                                         text instruction (e.g. "add a hat",
                                         "make the background a beach")

Both save the result as a PNG in image_cache/ next to this file and return
the local path so Kivy can display it in an Image widget.

Notes:
  - Requires an OpenAI API key (from platform.openai.com/api-keys). Paste
    the key exactly as OpenAI gives it to you (starts with "sk-").
  - Every call costs money on the linked OpenAI account. Nothing is
    generated or edited without a key.
  - This never uploads a picture anywhere except to the user's own
    OpenAI account for the single edit request being made.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import urllib.error
import urllib.request
import uuid

from database import load_settings, save_settings

API_BASE = "https://api.openai.com/v1"
GENERATIONS_URL = f"{API_BASE}/images/generations"
EDITS_URL = f"{API_BASE}/images/edits"
MODEL = "gpt-image-1"

IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image_cache")


# ---------------------------------------------------------------- settings

def get_image_key() -> str:
    return str(load_settings().get("image_api_key") or "").strip()


def save_image_key(key: str) -> None:
    settings = load_settings()
    settings["image_api_key"] = key.strip()
    save_settings(settings)


def has_image_key() -> bool:
    return bool(get_image_key())


def image_status() -> str:
    key = get_image_key()
    if not key:
        return "Image maker is off. Add an OpenAI API key."
    tail = key[-4:] if len(key) >= 4 else "****"
    return f"Image maker is on. Key ending {tail}."


def _auth_headers(key: str) -> dict:
    return {"Authorization": f"Bearer {key}"}


# ---------------------------------------------------------------- http helpers

def _raise_readable(exc: urllib.error.HTTPError):
    detail = exc.read().decode("utf-8", errors="ignore")[:220]
    raise RuntimeError(f"Image request error {exc.code}: {detail}") from exc


def _post_json(url: str, payload: dict, key: str) -> dict:
    headers = dict(_auth_headers(key))
    headers["Content-Type"] = "application/json"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        _raise_readable(exc)


def _post_multipart(url: str, fields: dict, files: dict, key: str) -> dict:
    """fields: {name: text_value}. files: {name: (file_path, mime_type)}."""
    boundary = uuid.uuid4().hex
    parts = []

    for name, value in fields.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(f"{value}\r\n".encode())

    for name, (file_path, mime_type) in files.items():
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        parts.append(f"Content-Type: {mime_type}\r\n\r\n".encode())
        parts.append(file_bytes)
        parts.append(b"\r\n")

    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)

    headers = dict(_auth_headers(key))
    headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        _raise_readable(exc)


def _save_b64_png(b64_data: str) -> str:
    os.makedirs(IMAGE_DIR, exist_ok=True)
    dest = os.path.join(IMAGE_DIR, f"image_{uuid.uuid4().hex[:8]}.png")
    with open(dest, "wb") as f:
        f.write(base64.b64decode(b64_data))
    return dest


def _first_b64(body: dict) -> str:
    data = body.get("data") or []
    if not data or "b64_json" not in data[0]:
        raise RuntimeError(f"No image came back: {body}")
    return data[0]["b64_json"]


# ---------------------------------------------------------------- public API

def generate_image(prompt: str, size: str = "1024x1024") -> str:
    """Create a brand new image from a text prompt. Returns a local file path."""
    key = get_image_key()
    if not key:
        raise RuntimeError("No image API key saved")
    if not prompt.strip():
        raise RuntimeError("Describe the picture you want first")

    payload = {"model": MODEL, "prompt": prompt.strip(), "size": size, "n": 1}
    body = _post_json(GENERATIONS_URL, payload, key)
    return _save_b64_png(_first_b64(body))


def edit_image(source_path: str, prompt: str, size: str = "1024x1024") -> str:
    """Change an existing image using a text instruction. Returns a local file path."""
    key = get_image_key()
    if not key:
        raise RuntimeError("No image API key saved")
    if not prompt.strip():
        raise RuntimeError("Describe the change you want first")
    if not source_path or not os.path.exists(source_path):
        raise RuntimeError("Pick a picture to edit first")

    mime_type = mimetypes.guess_type(source_path)[0] or "image/png"
    fields = {"model": MODEL, "prompt": prompt.strip(), "size": size, "n": "1"}
    files = {"image": (source_path, mime_type)}
    body = _post_multipart(EDITS_URL, fields, files, key)
    return _save_b64_png(_first_b64(body))


def clear_cache():
    """Delete old generated/edited images so they don't pile up on disk."""
    if not os.path.isdir(IMAGE_DIR):
        return
    for name in os.listdir(IMAGE_DIR):
        try:
            os.remove(os.path.join(IMAGE_DIR, name))
        except OSError:
            pass
