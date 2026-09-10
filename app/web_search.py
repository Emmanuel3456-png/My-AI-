"""Web search with a summarized answer for Quantum Mind.

Uses Tavily's search API (https://tavily.com), which is built for exactly
this: it returns a short synthesized answer plus the source pages it used,
so Quantum Mind does not need to guess at summarizing raw search results
itself. Same "bring your own key" pattern as Cloud, Avatar, and Image.

Notes:
  - Requires a Tavily API key (from app.tavily.com, free tier available).
    Keys usually start with "tvly-".
  - Every call uses that account's search quota.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

from database import load_settings, save_settings

SEARCH_URL = "https://api.tavily.com/search"


# ---------------------------------------------------------------- settings

def get_search_key() -> str:
    return str(load_settings().get("search_api_key") or "").strip()


def save_search_key(key: str) -> None:
    settings = load_settings()
    settings["search_api_key"] = key.strip()
    save_settings(settings)


def has_search_key() -> bool:
    return bool(get_search_key())


def search_status() -> str:
    key = get_search_key()
    if not key:
        return "Web search is off. Add a Tavily API key."
    tail = key[-4:] if len(key) >= 4 else "****"
    return f"Web search is on. Key ending {tail}."


# ---------------------------------------------------------------- search

def search_web(query: str, max_results: int = 5) -> dict:
    """Returns {"answer": str, "results": [{"title", "url", "content"}]}."""
    key = get_search_key()
    if not key:
        raise RuntimeError("No search API key saved")
    if not query.strip():
        raise RuntimeError("Say what you want to search for")

    payload = {
        "api_key": key,
        "query": query.strip(),
        "search_depth": "basic",
        "include_answer": True,
        "max_results": max_results,
    }
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(SEARCH_URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")[:220]
        raise RuntimeError(f"Search error {exc.code}: {detail}") from exc

    results = []
    for item in body.get("results", [])[:max_results]:
        results.append(
            {
                "title": item.get("title", "").strip(),
                "url": item.get("url", "").strip(),
                "content": item.get("content", "").strip(),
            }
        )
    return {"answer": (body.get("answer") or "").strip(), "results": results}


def format_search_reply(query: str, found: dict) -> dict:
    """Turns a search_web() result into a {"text", "url", "source"} reply."""
    answer = found.get("answer")
    results = found.get("results") or []
    if not answer and not results:
        return {"text": f"I could not find anything useful for \"{query}\"."}

    lines = []
    if answer:
        lines.append(answer)
    else:
        lines.append(f"Here is what I found for \"{query}\":")

    if results:
        titles = ", ".join(r["title"] for r in results[:4] if r.get("title"))
        if titles:
            lines.append(f"Sources: {titles}")

    reply = {"text": "\n".join(lines)}
    if results and results[0].get("url"):
        reply["url"] = results[0]["url"]
        reply["source"] = results[0].get("title") or "Source"
    return reply
