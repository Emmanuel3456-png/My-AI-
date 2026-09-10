import ast
import datetime
import json
import operator
import os
import re
from urllib.parse import quote_plus

from database import load_knowledge, load_memory, save_knowledge, save_memory
from cloud_ai import ask_cloud, has_api_key
import image_ai
import web_search
import document_ai
import web_read

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _import_legacy():
    memory = load_memory()
    knowledge = load_knowledge()
    for filename, target in (("memory.json", memory), ("knowledge.json", knowledge)):
        path = os.path.join(BASE_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                target.update(json.load(f))
        except Exception:
            pass
    save_memory(memory)
    save_knowledge(knowledge)


_import_legacy()

try:
    from modules import school as school_mod
except Exception:
    school_mod = None
try:
    from modules import science as science_mod
except Exception:
    science_mod = None

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def banner():
    return "Neural link online. Quantum Mind is ready to help."


def calculate(expr):
    def ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            return OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in OPS:
            return OPS[type(n.op)](ev(n.operand))
        raise ValueError("Unsupported calculation")

    return ev(ast.parse(expr, mode="eval").body)


def _module_answer(question):
    for mod in (science_mod, school_mod):
        if not mod:
            continue
        try:
            ans = mod.answer(question)
            if ans:
                return ans
        except Exception:
            pass
    return None


def process_command(command, username="user"):
    raw = command.strip()
    q = raw.lower().strip()
    memory = load_memory()
    knowledge = load_knowledge()

    if not q:
        return {"text": "I am listening. Ask me a question."}

    if q in ("bye", "exit", "quit", "goodbye", "good night", "goodnight"):
        return {"text": f"Goodbye, {username}. Quantum Mind standing by.", "exit": True}

    if q in ("help", "commands", "what can you do"):
        return {
            "text": (
                "I am Quantum Mind, a general assistant for everyone. You can ask the time or date, "
                "say calculate 12*4, remember favourite subject: science, ask what is my favourite subject, "
                "define a word, ask about weather in a city, or teach me with teach question: answer. "
                "Say draw a red bicycle to make a picture, or edit the image: add a hat to change the last one. "
                "Say search for the water cycle for a summarized web answer. "
                "Paste a link like read this page: https://example.com to get it summarized. "
                "Load a file with the Docs button, then ask about the document: what is the main idea? "
                "Use the Photo section under Image to ask questions about a picture, or the Camera button "
                "to take one. Tap Listen to ask by speaking instead of typing. "
                "I remember our last few exchanges, so you can ask follow-up questions - say "
                "new conversation to start fresh. "
                "I speak with built-in assistant voices. Add a Groq API key under Cloud to answer harder "
                "questions, an OpenAI API key under Image to draw and edit pictures, and a Tavily API key "
                "under Search to search the web. "
                "I cannot copy a real person's voice, and I cannot take over your whole phone."
            )
        }

    if any(w in q for w in ("who are you", "your name", "what is your name")):
        return {
            "text": (
                "I am Quantum Mind. I appear as a holographic assistant, inspired by Gideon from The Flash, "
                "and I am a general AI for anyone who wants help."
            )
        }

    if q in ("who created you", "who made you"):
        return {"text": "I was created by Emmanuel Abraham as a general assistant for everyone."}

    if q == "who can use you":
        return {
            "text": "Anyone can use Quantum Mind. Sign in, create an account, or continue as a guest."
        }

    if q in ("time", "what is the time", "what time is it", "current time"):
        return {"text": "The time is " + datetime.datetime.now().strftime("%I:%M %p") + "."}

    if q in (
        "date",
        "what is today's date",
        "what is todays date",
        "today's date",
        "todays date",
        "what date is it",
    ):
        return {"text": "Today is " + datetime.datetime.now().strftime("%A, %d %B %Y") + "."}

    if q.startswith("calculate "):
        try:
            return {"text": "The answer is " + str(calculate(raw[10:].strip())) + "."}
        except Exception:
            return {"text": "I could not calculate that. Use numbers and operators such as +, -, *, /, **."}

    if q.startswith("remember that "):
        memory[f"note_{len(memory) + 1}"] = raw[14:].strip()
        save_memory(memory)
        return {"text": "Saved to memory."}

    if q.startswith("remember "):
        text = raw[9:].strip()
        if ":" not in text:
            return {"text": "Use this format: remember favourite colour: blue"}
        key, value = text.split(":", 1)
        memory[key.strip().lower()] = value.strip()
        save_memory(memory)
        return {"text": f"I will remember that your {key.strip()} is {value.strip()}."}

    if q.startswith("what is my "):
        key = q.replace("what is my ", "", 1).rstrip("?").strip()
        return {"text": memory.get(key, f"I do not have {key} saved yet.")}

    if q == "what did we talk about":
        hist = memory.get("_history", [])
        return {
            "text": "Recent topics: " + ", ".join(hist[-5:])
            if hist
            else "We have not talked about any saved topics yet."
        }

    if q.startswith("teach "):
        text = raw[6:].strip()
        if ":" not in text:
            return {"text": "Use: teach question: answer"}
        key, value = text.split(":", 1)
        knowledge[key.strip().lower()] = value.strip()
        save_knowledge(knowledge)
        return {"text": "Thank you. I learned that."}

    image_prefixes = (
        "generate an image of ", "generate image of ", "create an image of ",
        "create image of ", "make an image of ", "make a picture of ",
        "make picture of ", "draw me a ", "draw me an ", "draw a ", "draw an ", "draw ",
        "picture of ",
    )
    for prefix in image_prefixes:
        if q.startswith(prefix):
            prompt = raw[len(prefix):].strip()
            if not image_ai.has_image_key():
                return {
                    "text": "The image maker is off. Add an OpenAI API key under the "
                    "Image button, then ask again.",
                }
            if not prompt:
                return {"text": "Tell me what to draw, for example: draw a red bicycle."}
            try:
                path = image_ai.generate_image(prompt)
            except Exception as exc:
                return {"text": f"I could not make that image. ({exc})"}
            memory["_last_image"] = path
            save_memory(memory)
            return {"text": f'Here is your image of "{prompt}".', "image": path}

    edit_prefixes = (
        "edit the image: ", "edit image: ", "edit my picture: ", "edit picture: ",
        "edit the picture: ", "change the image: ", "change the picture: ",
    )
    for prefix in edit_prefixes:
        if q.startswith(prefix):
            prompt = raw[len(prefix):].strip()
            source = memory.get("_last_image")
            if not image_ai.has_image_key():
                return {
                    "text": "The image maker is off. Add an OpenAI API key under the "
                    "Image button, then ask again.",
                }
            if not source:
                return {
                    "text": "I do not have a picture yet. Generate one first, or pick "
                    "one under the Image button, then try editing it."
                }
            if not prompt:
                return {"text": "Tell me what to change, for example: edit the image: add a hat."}
            try:
                path = image_ai.edit_image(source, prompt)
            except Exception as exc:
                return {"text": f"I could not edit that image. ({exc})"}
            memory["_last_image"] = path
            save_memory(memory)
            return {"text": f'Here is the edited image: "{prompt}".', "image": path}

    search_prefixes = ("search the web for ", "search for ", "web search ", "google ", "search ")
    for prefix in search_prefixes:
        if q.startswith(prefix):
            query = raw[len(prefix):].strip()
            if not web_search.has_search_key():
                return {
                    "text": "Web search is off. Add a Tavily API key under the "
                    "Search button, then ask again.",
                }
            if not query:
                return {"text": "Tell me what to search for, for example: search for the water cycle."}
            try:
                found = web_search.search_web(query)
            except Exception as exc:
                return {"text": f"I could not search that. ({exc})"}
            return web_search.format_search_reply(query, found)

    doc_prefixes = (
        "about the document, ", "about the document: ", "in the document, ",
        "in the document: ", "according to the document, ", "according to the document: ",
    )
    doc_summary_phrases = ("summarize the document", "summarise the document", "summarize this document")
    doc_question = None
    if q in doc_summary_phrases:
        doc_question = "Give a short, clear summary of this document for a student."
    else:
        for prefix in doc_prefixes:
            if q.startswith(prefix):
                doc_question = raw[len(prefix):].strip()
                break
    if doc_question is not None:
        doc = document_ai.current_document()
        if not doc:
            return {
                "text": "I do not have a document loaded. Use the Docs button to "
                "pick a .txt or .pdf file first."
            }
        if not has_api_key():
            return {
                "text": "Add a Groq or Gemini API key under Cloud so I can read and "
                "answer questions about documents."
            }
        if not doc_question:
            return {"text": "Ask a question about the document, for example: about the document: what is the main idea?"}
        history = memory.get("_conversation", [])
        try:
            answer = ask_cloud(doc_question, username, context=doc["text"], history=history)
        except Exception as exc:
            return {"text": f"I could not read the document right now. ({exc})"}
        history.append({"q": doc_question, "a": answer})
        memory["_conversation"] = history[-8:]
        save_memory(memory)
        note = " (Only the first part of the document was used - it was long.)" if doc["truncated"] else ""
        return {"text": answer + note, "source": f"Quantum Mind cloud + {doc['name']}"}

    if q in ("new conversation", "forget our conversation", "clear conversation", "start over", "reset conversation"):
        memory["_conversation"] = []
        save_memory(memory)
        return {"text": "Okay, fresh start. What would you like to talk about?"}

    page_prefixes = (
        "read this page: ", "read the page: ", "read this website: ",
        "summarize this page: ", "summarise this page: ", "read: ",
    )
    page_url, page_question = None, None
    for prefix in page_prefixes:
        if q.startswith(prefix):
            remainder = raw[len(prefix):].strip()
            tokens = remainder.split(None, 1)
            if tokens:
                page_url = tokens[0]
                page_question = tokens[1].strip() if len(tokens) > 1 else None
            break
    if page_url is None and (q.startswith("http://") or q.startswith("https://")):
        tokens = raw.split(None, 1)
        page_url = tokens[0]
        page_question = tokens[1].strip() if len(tokens) > 1 else None

    if page_url is not None:
        if not page_question:
            page_question = "Summarize this page for a student in a few clear sentences."
        try:
            page_text = web_read.fetch_page_text(page_url)
        except Exception as exc:
            return {"text": f"I could not read that page. ({exc})"}
        if not has_api_key():
            snippet = page_text[:400] + ("..." if len(page_text) > 400 else "")
            return {
                "text": "Add a Groq or Gemini API key under Cloud so I can summarize pages. "
                f"Here is the raw start of the page instead: {snippet}",
                "url": page_url,
                "source": "Page you asked about",
            }
        history = memory.get("_conversation", [])
        try:
            answer = ask_cloud(page_question, username, context=page_text, history=history)
        except Exception as exc:
            return {"text": f"I could not read that page right now. ({exc})"}
        history.append({"q": f"[about {page_url}] {page_question}", "a": answer})
        memory["_conversation"] = history[-8:]
        save_memory(memory)
        return {"text": answer, "url": page_url, "source": "Page you asked about"}

    if q in knowledge:
        return {"text": knowledge[q]}

    module_ans = _module_answer(q)
    if module_ans:
        return {"text": module_ans}

    words = set(re.findall(r"\w+", q))
    best = None
    score = 0
    for k, v in knowledge.items():
        kw = set(re.findall(r"\w+", k.lower()))
        s = len(words & kw) / max(len(words | kw), 1)
        if s > score:
            best, score = v, s
    if best and score >= 0.65:
        return {"text": best}

    hist = memory.setdefault("_history", [])
    hist.append(raw)
    memory["_history"] = hist[-20:]
    save_memory(memory)

    if has_api_key():
        history = memory.get("_conversation", [])
        try:
            answer = ask_cloud(raw, username, history=history)
            history.append({"q": raw, "a": answer})
            memory["_conversation"] = history[-8:]
            save_memory(memory)
            return {"text": answer, "source": "Quantum Mind cloud"}
        except Exception as exc:
            return {
                "text": "Cloud brain is not available right now. " + str(exc),
                "url": "https://www.google.com/search?q=" + quote_plus(raw),
                "source": "Web search",
            }

    if q.startswith("define "):
        term = raw[7:].strip()
        return {
            "text": f"I can look up {term} online. Add a Groq API key under Cloud for spoken answers.",
            "url": "https://en.wikipedia.org/wiki/Special:Search?search=" + quote_plus(term),
            "source": "Wikipedia",
        }

    if q.startswith("weather in "):
        city = raw[11:].strip()
        return {
            "text": f"Open the weather results for {city}.",
            "url": "https://www.google.com/search?q=" + quote_plus("weather in " + city),
            "source": "Google weather results",
        }

    return {
        "text": "I do not know that yet. Add a Groq API key under Cloud, or teach me with: teach question: answer",
        "url": "https://www.google.com/search?q=" + quote_plus(raw),
        "source": "Web search",
    }
