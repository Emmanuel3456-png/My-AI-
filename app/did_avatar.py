"""D-ID talking avatar integration for Quantum Mind.

Turns a reply into a short video of the assistant's face speaking it,
using D-ID's REST API (https://docs.d-id.com).

Flow for each reply:
  1. upload_face_image()  -> uploads gideon_face.jpg once, gets a hosted URL
  2. create_talk()        -> asks D-ID to animate that face saying the text
  3. wait_for_talk()      -> polls until D-ID finishes rendering
  4. download_video()     -> saves the finished mp4 locally so Kivy can play it

Notes:
  - Requires a D-ID API key (from studio.d-id.com -> API Keys). Paste the
    key exactly as D-ID gives it to you.
  - D-ID's exact field names occasionally change between API versions -
    if you get 400/401 errors, check https://docs.d-id.com/reference/createtalk
    against the payload built in create_talk() below.
  - Every call to generate_talk() costs D-ID render minutes on your plan.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
import uuid

from database import load_settings, save_settings

API_BASE = "https://api.d-id.com"
IMAGES_URL = f"{API_BASE}/images"
TALKS_URL = f"{API_BASE}/talks"

VIDEO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "avatar_cache")
FACE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gideon_face.jpg")


# ---------------------------------------------------------------- settings

def get_did_key() -> str:
    return str(load_settings().get("did_api_key") or "").strip()


def save_did_key(key: str) -> None:
    settings = load_settings()
    settings["did_api_key"] = key.strip()
    # A new key means any previously uploaded face URL is no longer valid
    settings.pop("did_face_url", None)
    save_settings(settings)


def has_did_key() -> bool:
    return bool(get_did_key())


def did_status() -> str:
    key = get_did_key()
    if not key:
        return "Talking avatar is off. Add a D-ID API key."
    tail = key[-4:] if len(key) >= 4 else "****"
    return f"Talking avatar is on. Key ending {tail}."


def _auth_header(key: str) -> dict:
    # D-ID dashboard keys are typically already base64 "username:password"
    # style credentials - used directly as a Basic auth token.
    return {"Authorization": f"Basic {key}"}


# ---------------------------------------------------------------- http helpers

def _http_json(url: str, payload: dict | None, headers: dict, method: str = "POST") -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_multipart_image(url: str, file_path: str, headers: dict) -> dict:
    boundary = uuid.uuid4().hex
    filename = os.path.basename(file_path)
    mime_type = mimetypes.guess_type(filename)[0] or "image/jpeg"

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    parts = []
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode()
    )
    parts.append(f"Content-Type: {mime_type}\r\n\r\n".encode())
    parts.append(file_bytes)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req_headers = dict(headers)
    req_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _raise_readable(exc: urllib.error.HTTPError):
    detail = exc.read().decode("utf-8", errors="ignore")[:220]
    raise RuntimeError(f"D-ID error {exc.code}: {detail}") from exc


# ---------------------------------------------------------------- steps

def upload_face_image(force: bool = False) -> str:
    """Upload gideon_face.jpg to D-ID once, cache the hosted URL in settings."""
    settings = load_settings()
    cached = settings.get("did_face_url")
    if cached and not force:
        return cached

    key = get_did_key()
    if not key:
        raise RuntimeError("No D-ID API key saved")
    if not os.path.exists(FACE_PATH):
        raise RuntimeError(f"Face image not found at {FACE_PATH}")

    try:
        body = _http_multipart_image(IMAGES_URL, FACE_PATH, _auth_header(key))
    except urllib.error.HTTPError as exc:
        _raise_readable(exc)

    url = body.get("url") or body.get("image_url")
    if not url:
        raise RuntimeError(f"D-ID did not return an image URL: {body}")

    settings["did_face_url"] = url
    save_settings(settings)
    return url


def create_talk(source_url: str, text: str) -> str:
    key = get_did_key()
    if not key:
        raise RuntimeError("No D-ID API key saved")

    payload = {
        "source_url": source_url,
        "script": {
            "type": "text",
            "input": text,
            "provider": {"type": "microsoft", "voice_id": "en-US-GuyNeural"},
        },
        "config": {"fluent": True, "stitch": True},
    }
    headers = dict(_auth_header(key))
    headers["Content-Type"] = "application/json"
    try:
        body = _http_json(TALKS_URL, payload, headers, method="POST")
    except urllib.error.HTTPError as exc:
        _raise_readable(exc)

    talk_id = body.get("id")
    if not talk_id:
        raise RuntimeError(f"D-ID did not return a talk id: {body}")
    return talk_id


def wait_for_talk(talk_id: str, timeout: float = 60.0, interval: float = 2.0) -> str:
    """Poll D-ID until the talk is done. Returns the finished video URL."""
    key = get_did_key()
    headers = _auth_header(key)
    url = f"{TALKS_URL}/{talk_id}"
    waited = 0.0
    while waited < timeout:
        try:
            body = _http_json(url, None, headers, method="GET")
        except urllib.error.HTTPError as exc:
            _raise_readable(exc)
        status = body.get("status")
        if status == "done":
            result_url = body.get("result_url")
            if not result_url:
                raise RuntimeError(f"D-ID marked talk done but gave no video: {body}")
            return result_url
        if status == "error":
            raise RuntimeError(f"D-ID failed to render: {body.get('error', body)}")
        time.sleep(interval)
        waited += interval
    raise RuntimeError("Timed out waiting for D-ID to finish rendering")


def download_video(video_url: str) -> str:
    os.makedirs(VIDEO_DIR, exist_ok=True)
    dest = os.path.join(VIDEO_DIR, f"reply_{uuid.uuid4().hex[:8]}.mp4")
    req = urllib.request.Request(video_url)
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as f:
        f.write(resp.read())
    return dest


def generate_talk(text: str) -> str:
    """Full pipeline: text -> local mp4 path of the face speaking it."""
    if not text.strip():
        raise RuntimeError("Nothing to say")
    source_url = upload_face_image()
    talk_id = create_talk(source_url, text)
    video_url = wait_for_talk(talk_id)
    return download_video(video_url)


def clear_cache():
    """Delete old downloaded reply videos so they don't pile up on disk."""
    if not os.path.isdir(VIDEO_DIR):
        return
    for name in os.listdir(VIDEO_DIR):
        try:
            os.remove(os.path.join(VIDEO_DIR, name))
        except OSError:
            pass
