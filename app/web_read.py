"""Read-a-webpage for Quantum Mind.

This is deliberately narrow: given one URL the student names, it fetches
that page's own text and lets the Cloud model answer questions about it
or summarize it. It does not click links, submit forms, log into
anything, or visit any page the student did not explicitly name -
Quantum Mind cannot go "browse the web" on its own.

No key of its own is needed to fetch a page; a Cloud key (Groq or
Gemini, added under the Cloud button) is needed to summarize/answer
questions about what was fetched.
"""
from __future__ import annotations

import re
import urllib.error
import urllib.request

MAX_CHARS = 8000
_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b[^<]*(?:(?!</\1>)<[^<]*)*</\1>", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")


def _looks_like_url(text: str) -> bool:
    return bool(re.match(r"^https?://", text.strip(), re.IGNORECASE))


def fetch_page_text(url: str) -> str:
    if not _looks_like_url(url):
        raise RuntimeError("That does not look like a web address (needs http:// or https://)")

    req = urllib.request.Request(url, headers={"User-Agent": "QuantumMind-Assistant/3.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read(2_000_000)  # cap what we pull down
            charset = resp.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Could not open that page (error {exc.code})") from exc
    except Exception as exc:
        raise RuntimeError(f"Could not open that page. ({exc})") from exc

    html = raw.decode(charset, errors="ignore")
    html = _SCRIPT_STYLE_RE.sub(" ", html)
    text = _TAG_RE.sub(" ", html)
    text = _WS_RE.sub(" ", text).strip()

    if not text:
        raise RuntimeError("That page had no readable text")
    return text[:MAX_CHARS]
