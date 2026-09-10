# Quantum Mind 3.0

General assistant for everyone.

## What this version does
- Shows a holographic Gideon-style face while you use the assistant
- Speaks answers with built-in assistant voices (Quantum, Calm Guide, Bright Helper, Teacher)
- Uses a Groq or Gemini API key for harder questions, and remembers the last few
  exchanges so you can ask follow-up questions (Cloud button)
- Draws new pictures and edits existing ones with an OpenAI API key (Image button)
- Answers questions about a picture you show it or take with the camera
  (Image button, "Ask about a picture")
- Searches the web and gives a short summarized answer with sources (Search button)
- Reads a .txt/.md/.pdf file and answers questions about it, including a best-effort
  read of scanned/image PDF pages (Docs button)
- Reads a single webpage you link and summarizes or answers questions about it
  (say "read this page: https://...")
- Takes spoken questions instead of typed ones (microphone button)
- Takes a photo directly with the camera instead of only picking an existing one
- Optional accounts (sign in, create account, or continue as guest), memory, teach-me knowledge, time, date, and calculator
- Looks like a holographic HUD home screen (neon frames, scan line, quantum face) instead of a plain chatbot box

## What this version does not do, and why
- **No live, always-on voice conversation.** Voice input is one question at a time,
  only while you are tapping the microphone button. An always-listening microphone
  on a children's device is a real privacy risk, not just a technical feature.
- **No autonomous web browsing or taking actions** (clicking things, filling out
  forms, logging into sites, sending emails, buying things). "Read this page" only
  ever opens the one link you give it - it cannot decide to visit other pages or
  act on your behalf.
- **No Google Workspace / Calendar / Gmail / CapCut integrations.** Connecting a
  school app to student Google accounts needs the school to register its own
  Google Cloud OAuth project and make a deliberate decision about that access -
  it is not something to bolt on quietly.
- **No video generation.**
- **No cloning of a real person's voice or face**, and **no taking over a whole
  phone** (contacts, messages, files) beyond what is described above.
- **No real OCR engine.** Scanned PDF pages are instead shown to the same vision
  model used for pictures and asked to transcribe them - this needs a Cloud API
  key and the `pymupdf` package, and is capped at 5 pages per document so it
  cannot run up a surprise bill.
- **No drawing/editing pictures of real people**, or anything against OpenAI's
  usage rules.
- It is not the official Gemini app and is not trying to be one - it is a general assistant project that borrows the same idea (one assistant, several abilities) using
  separate cloud services you connect yourself.

## Feature checklist
A plain answer to "does it have X", using the common way people describe modern
assistants:

| Feature | Status |
|---|---|
| Understands typos/slang | Basic - built-in commands need close matches; cloud questions (Groq/Gemini) handle typos and slang well |
| Reasoning / math / logic | Yes - calculator plus full reasoning through the Cloud key |
| Memory (name, preferences, recent chat) | Yes - saved facts, plus the last ~8 exchanges of conversation |
| Up-to-date knowledge + web search | Yes, via Search (Tavily) |
| Writing (emails, code, stories, posts) | Yes, through the Cloud key - no dedicated "tone profile" beyond what you tell it in the conversation |
| Voice (talk and listen) | Yes - speaks built-in voices, listens via microphone button |
| Image generation | Yes, via Image (OpenAI) |
| Image understanding | Yes - upload or take a photo, ask about it |
| Video generation | No |
| File handling (PDF/docs/code) | Yes for txt/md/pdf, including a best-effort read of scanned pages |
| Tool use (search/images/etc as needed) | Yes, but only when you ask for that tool by name/phrase - it does not silently pick tools for you |
| Task execution (reminders, sending email, playlists) | No |
| Integrations (Calendar, Gmail, CapCut, etc) | No - see above |
| Learns your style/name/tone/goals | Partial - saves facts you tell it to remember; does not automatically infer tone |
| Personality (friendly, jokes) | Basic - a consistent assistant character, not a distinct comedic personality |
| Safety | Yes - stays inside built-in guardrails and the same rules any Anthropic/OpenAI/Google-backed key already enforces |
| Proactivity (suggests before asked) | No - only responds to what you ask |
| Long context / big documents | Partial - documents are read up to ~12,000 characters and conversation history up to ~8 exchanges, not unlimited |
| API access for other apps | No - this is the app, not a service other apps call |
| Fine-tuning on your data | No |
| Function calling | Internally yes (the app's own commands dispatch actions); not exposed for outside developers |
| Streaming responses | No - answers arrive as one finished reply, not word-by-word |

## Add a Groq or Gemini API key (harder questions, document Q&A, conversation memory)
1. Ask a parent or teacher to open https://console.groq.com/keys (or Gemini's
   equivalent at https://aistudio.google.com/apikey)
2. Create an API key
3. Open Quantum Mind, tap **Cloud**, paste the key, tap **Save key**
4. Ask a normal question such as "explain photosynthesis simply", then a
   follow-up like "explain that more simply" - it remembers the last exchange

Do not send the key to anyone, including chat apps. You can tap **Remove key** later.
Say "new conversation" any time to make it forget recent context and start fresh.

## Add an OpenAI API key (draw/edit/discuss pictures)
1. Ask a parent or teacher to open https://platform.openai.com/api-keys
2. Create an API key (this uses that account's paid image credits)
3. Open Quantum Mind, tap **Image**, paste the key, tap **Save key**
4. Type a request such as "draw a red bicycle in a park", or use the popup's
   "Generate new image" button
5. To change a picture, say "edit the image: add a birthday hat", or use the
   popup to browse for or photograph any picture and edit it
6. To ask questions about a picture (needs a Cloud key too), use the popup's
   "Ask about a picture" section - browse for one or take a new photo

Generated and edited pictures are saved locally in `image_cache/`; camera photos
are saved in `camera_cache/`.

## Add a Tavily API key (web search)
1. Ask a parent or teacher to open https://app.tavily.com (free tier available)
2. Create an API key
3. Open Quantum Mind, tap **Search**, paste the key, tap **Save key**
4. Ask things like "search for the water cycle"

## Read a document (Docs button)
1. Tap **Docs**, browse for a `.txt`, `.md`, or `.pdf` file, tap **Load document**
2. Ask "about the document: what is the main idea?" or "summarize the document"
   (needs a Groq or Gemini key added under Cloud)

If a PDF page turns out to be a scanned image with no selectable text, and you
have a Cloud key saved and the `pymupdf` package installed, Quantum Mind will
try reading up to 5 such pages using the vision model and tell you how many it
managed.

## Read a webpage
Say "read this page: https://example.com" or just paste a link on its own, and
Quantum Mind will fetch that one page and summarize it (needs a Cloud key for
the summary; without one it shows you the raw start of the page instead). It
will not follow links from that page or take any action - only the page you name.

## Voice input
Tap the microphone button next to Ask and speak your question. On a phone this
uses Android's own on-device speech recognizer through a normal system dialog -
no separate key is needed, and it only listens for that one question.

## Camera
Tap "Take a photo" wherever you'd normally browse for a picture (inside the
Image popup). It opens the phone's own camera app and hands the saved photo
back to Quantum Mind - no background or silent camera access.

## How to run on a computer
```bash
pip install kivy pypdf pymupdf
python Main.py
```

`pymupdf` is optional - only needed for reading scanned PDF pages. Voice input
on desktop is optional and needs `pip install SpeechRecognition pyaudio`;
without either, typing and picking existing files still works exactly the same.

Optional accounts. You can continue as guest, or create your own login.

A leftover admin account from early builds still exists until you change it:
- username: `admin`
- password: `admin123`

## How to build an Android APK
You need Buildozer on Linux:
```bash
buildozer android debug
```

`pymupdf` is a compiled package - it is not guaranteed to build for Android
through python-for-android. Test a real build before relying on scanned-PDF
reading on a phone; everything else in this list has a plain-Python or
plyer/pyjnius path that is much more likely to build cleanly.

On a phone, tap **Voice** to pick a speaking style. Type a request and tap **Ask**,
or tap the microphone to speak it. Quantum Mind will show the answer on screen and
speak it if the phone supports text-to-speech.
