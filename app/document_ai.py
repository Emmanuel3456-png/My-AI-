"""Document reading for Quantum Mind.

Loads a .txt/.md/.pdf file into memory so the student can ask questions
about it or get it summarized. No key is needed to load a document; a
Cloud API key (Groq or Gemini, added under the Cloud button) is needed to
actually answer questions about it, since that is what reads and reasons
over the text.

PDF text is pulled out with pypdf first. If a PDF page has no selectable
text (a scanned page saved as an image), Quantum Mind does not have a
real OCR engine, but it can fall back to showing that page to the same
vision-capable Cloud model used for "ask about a picture" and asking it
to transcribe what it sees. That fallback:
  - only runs if a Cloud API key is saved (it is a real API call)
  - only runs if the `pymupdf` package is installed, to turn the PDF
    page into an image
  - is capped to a handful of pages so one big scanned PDF cannot rack
    up a large bill by accident
"""
from __future__ import annotations

import os
import tempfile

from database import load_memory, save_memory

MAX_CHARS = 12000  # keeps prompts to the cloud model a reasonable size
MAX_OCR_PAGES = 5  # cap on how many scanned pages we will vision-read per load

TRANSCRIBE_PROMPT = (
    "Transcribe every word of readable text in this document page, in "
    "reading order. Reply with only the transcribed text, nothing else. "
    "If there is no readable text, reply with an empty response."
)


def _read_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _read_pdf_text(path: str):
    """Returns (page_texts, blank_page_indices)."""
    try:
        from pypdf import PdfReader
    except Exception as exc:
        raise RuntimeError(
            "PDF reading needs the pypdf package. Run: pip install pypdf"
        ) from exc

    reader = PdfReader(path)
    page_texts = []
    blank_pages = []
    for i, page in enumerate(reader.pages):
        try:
            text = (page.extract_text() or "").strip()
        except Exception:
            text = ""
        page_texts.append(text)
        if not text:
            blank_pages.append(i)
    return page_texts, blank_pages


def _ocr_pages_with_vision(path: str, page_indices):
    """Rasterizes the given pages and asks the vision model to read them.
    Returns {page_index: text}. Silently skips pages it cannot handle."""
    try:
        import fitz  # PyMuPDF
    except Exception:
        return {}

    from cloud_ai import ask_cloud_about_image, has_api_key

    if not has_api_key():
        return {}

    results = {}
    doc = fitz.open(path)
    try:
        for i in page_indices[:MAX_OCR_PAGES]:
            if i >= doc.page_count:
                continue
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=150)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                pix.save(tmp_path)
                text = ask_cloud_about_image(TRANSCRIBE_PROMPT, tmp_path, "document reader")
                text = (text or "").strip()
                if text:
                    results[i] = text
            except Exception:
                continue
            finally:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
    finally:
        doc.close()
    return results


def extract_text(path: str):
    """Returns (text, note). note explains any OCR fallback that happened."""
    if not path or not os.path.exists(path):
        raise RuntimeError("That file does not exist")
    ext = os.path.splitext(path)[1].lower()

    if ext in (".txt", ".md", ".csv"):
        text = _read_txt(path).strip()
        if not text:
            raise RuntimeError("No readable text was found in that file")
        return text, ""

    if ext != ".pdf":
        raise RuntimeError("Quantum Mind can read .txt, .md, and .pdf files")

    page_texts, blank_pages = _read_pdf_text(path)
    note = ""

    if blank_pages:
        ocr_results = _ocr_pages_with_vision(path, blank_pages)
        if ocr_results:
            for i, text in ocr_results.items():
                page_texts[i] = text
            read_count = len(ocr_results)
            skipped = len(blank_pages) - read_count
            note = f"{read_count} scanned page(s) were read using the Cloud vision model."
            if skipped > 0:
                note += f" {skipped} scanned page(s) were left out (past the {MAX_OCR_PAGES}-page limit)."
        else:
            note = (
                f"{len(blank_pages)} page(s) looked like scanned images with no "
                "selectable text and could not be read (needs a Cloud API key "
                "under Cloud, and the pymupdf package installed)."
            )

    text = "\n".join(t for t in page_texts if t).strip()
    if not text:
        raise RuntimeError(
            "No readable text was found in that PDF. It may be fully scanned "
            "images - add a Cloud API key under Cloud and install pymupdf to "
            "let Quantum Mind read scanned pages."
        )
    return text, note


def load_document(path: str):
    """Extracts, truncates, and remembers a document. Returns (name, word_count, note)."""
    text, note = extract_text(path)
    word_count = len(text.split())
    truncated = text[:MAX_CHARS]

    memory = load_memory()
    memory["_doc_text"] = truncated
    memory["_doc_name"] = os.path.basename(path)
    memory["_doc_truncated"] = len(text) > MAX_CHARS
    save_memory(memory)
    return os.path.basename(path), word_count, note


def current_document():
    memory = load_memory()
    text = memory.get("_doc_text")
    if not text:
        return None
    return {
        "name": memory.get("_doc_name", "document"),
        "text": text,
        "truncated": bool(memory.get("_doc_truncated")),
    }


def clear_document() -> None:
    memory = load_memory()
    memory.pop("_doc_text", None)
    memory.pop("_doc_name", None)
    memory.pop("_doc_truncated", None)
    save_memory(memory)
