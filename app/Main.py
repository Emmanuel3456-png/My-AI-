from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
import os
import threading
import webbrowser

from hud import (
    AMBER,
    CYAN,
    FACE_PATH,
    GLOW_TEXT,
    MUTED_TEXT,
    TEAL,
    ClockLabel,
    FacePanel,
    FramePanel,
    HudField,
    NeonButton,
    Stage,
    glow_label,
    styled_popup,
)

from Brain import banner, process_command
from cloud_ai import ask_cloud_about_image, has_api_key, key_status, save_api_key
from database import hash_pass, load_memory, load_users, save_memory, save_users
from voice import VOICE_PROFILES, speak, stop_speaking
import camera_input
import did_avatar
import document_ai
import image_ai
import voice_input
import web_search


Window.clearcolor = (0.004, 0.01, 0.03, 1)

class QMApp(App):
    title = "Quantum Mind  •  Neural Core"

    def build(self):
        self.username = None
        self.role = None
        self.voice_profile = "quantum"
        self.pending_url = None
        self.pending_source = None
        self._type_event = None
        self.last_image_path = load_memory().get("_last_image")
        self.stage = Stage()
        self.stage.set_content(self.login_screen())
        return self.stage

    def label(self, text, size=18, color=None):
        lbl = Label(text=text, font_size=dp(size), color=color or GLOW_TEXT, markup=True)
        return lbl

    def tint_button(self, text, callback, height=54):
        b = NeonButton(text=text, size_hint_y=None, height=dp(height))
        b.bind(on_release=callback)
        return b

    def hud_popup(self, title, content, size_hint=(0.94, 0.72)):
        return styled_popup(title, content, size_hint=size_hint)

    def login_screen(self):
        root = BoxLayout(orientation="vertical", padding=dp(22), spacing=dp(10))
        face = Image(
            source=FACE_PATH,
            allow_stretch=True,
            keep_ratio=True,
            size_hint_y=0.42,
        )
        root.add_widget(face)
        root.add_widget(
            self.label(
                "[b]QUANTUM MIND[/b]\n[size=15]GENERAL ASSISTANT  •  OPEN TO EVERYONE[/size]",
                26,
            )
        )
        self.user = HudField(hint_text="USERNAME", size_hint_y=None, height=dp(50))
        self.password = HudField(
            hint_text="PASSWORD", password=True, size_hint_y=None, height=dp(50)
        )
        msg = self.label("", 14, color=AMBER)
        root.add_widget(self.user)
        root.add_widget(self.password)
        actions = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        actions.add_widget(self.tint_button("SIGN IN", lambda *_: self.do_login(msg), height=50))
        actions.add_widget(self.tint_button("CREATE ACCOUNT", lambda *_: self.do_register(msg), height=50))
        root.add_widget(actions)
        root.add_widget(self.tint_button("CONTINUE AS GUEST", lambda *_: self.enter_as("guest", "user"), height=48))
        root.add_widget(msg)
        root.add_widget(self.label("[size=12]FREE TO USE  •  SIGN IN OPTIONAL[/size]", 12, color=MUTED_TEXT))
        return root

    def enter_as(self, username, role):
        self.username = username
        self.role = (role or "user").lower()
        self._run_boot()

    def do_login(self, msg):
        u = self.user.text.strip().lower()
        p = self.password.text
        if not u:
            msg.text = "Enter a username, or continue as guest."
            return
        data = load_users().get(u)
        if data and data.get("password") in (p, hash_pass(p)):
            self.enter_as(u, data.get("role", "user"))
        else:
            msg.text = "No match. Create an account, or continue as guest."

    def do_register(self, msg):
        u = self.user.text.strip().lower()
        p = self.password.text
        if len(u) < 3 or not u.replace("_", "").isalnum():
            msg.text = "Choose a username with 3+ letters or numbers."
            return
        if u in ("guest", "admin"):
            msg.text = "That name is reserved. Pick another."
            return
        if len(p) < 4:
            msg.text = "Choose a password with at least 4 characters."
            return
        users = load_users()
        if u in users:
            msg.text = "That username is taken. Sign in, or pick another."
            return
        users[u] = {"password": hash_pass(p), "role": "user"}
        save_users(users)
        self.enter_as(u, "user")

    def _run_boot(self):
        box = BoxLayout(orientation="vertical", padding=dp(28), spacing=dp(12))
        status = Label(
            text="ESTABLISHING NEURAL LINK",
            font_size=dp(18),
            color=CYAN,
            bold=True,
            markup=True,
        )
        detail = Label(text="", font_size=dp(14), color=MUTED_TEXT)
        box.add_widget(self.label("[b]QUANTUM MIND[/b]", 22))
        box.add_widget(status)
        box.add_widget(detail)
        self.stage.set_content(box)
        steps = [
            ("Opening a public session...", 0.35),
            ("Loading memory core...", 0.7),
            ("Aligning holographic face...", 1.05),
            ("Calibrating voice channel...", 1.4),
            (f"Welcome, {self.username}. Core online.", 1.8),
        ]

        def apply(i, text):
            def _do(*_):
                detail.text = text
                status.text = f"SYSTEMS  •  {i + 1}/{len(steps)}"
            return _do

        for i, (text, delay) in enumerate(steps):
            Clock.schedule_once(apply(i, text), delay)
        Clock.schedule_once(lambda *_: self._enter_assistant(), 2.2)

    def _enter_assistant(self):
        self.stage.set_content(self.assistant_screen())
        Clock.schedule_once(
            lambda *_: speak(banner() + f" Welcome, {self.username}.", self.voice_profile),
            0.35,
        )

    def assistant_screen(self):
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))

        header = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(6))
        header.add_widget(self.label(f"[b]QM-3  //  {self.username.upper()}[/b]", 13))
        header.add_widget(ClockLabel(size_hint_x=0.55))
        root.add_widget(header)

        top = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        modules = [
            ("VOICE", self.voice_popup),
            ("CLOUD", self.cloud_popup),
            ("AVATAR", self.avatar_popup),
            ("IMAGE", self.image_popup),
            ("SEARCH", self.search_popup),
            ("DOCS", self.docs_popup),
        ]
        if self.role == "admin":
            modules.append(("ADMIN", self.admin_popup))
        for label, handler in modules:
            btn = NeonButton(text=label, size_hint_x=0.16, font_size=dp(10))
            btn.bind(on_release=handler)
            top.add_widget(btn)
        root.add_widget(top)

        self.face_panel = FacePanel(size_hint_y=0.52)
        root.add_widget(self.face_panel)

        reply_wrap = FloatLayout(size_hint_y=None, height=dp(78))
        reply_wrap.add_widget(FramePanel(size_hint=(1, 1), pos_hint={"x": 0, "y": 0}))
        self.spoken = Label(
            text=banner(),
            font_size=dp(15),
            color=GLOW_TEXT,
            size_hint=(0.94, 0.88),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            text_size=(Window.width - dp(48), dp(70)),
            halign="center",
            valign="middle",
        )
        reply_wrap.add_widget(self.spoken)
        root.add_widget(reply_wrap)

        log_wrap = FloatLayout(size_hint_y=0.22)
        log_wrap.add_widget(FramePanel(size_hint=(1, 1), pos_hint={"x": 0, "y": 0}))
        scroll = ScrollView(size_hint=(0.96, 0.9), pos_hint={"center_x": 0.5, "center_y": 0.5})
        self.log = Label(
            text="[i]// conversation log[/i]\n",
            size_hint_y=None,
            text_size=(Window.width - dp(48), None),
            valign="top",
            markup=True,
            color=MUTED_TEXT,
            font_size=dp(13),
        )
        self.log.bind(texture_size=lambda inst, val: setattr(inst, "height", val[1] + dp(12)))
        scroll.add_widget(self.log)
        log_wrap.add_widget(scroll)
        root.add_widget(log_wrap)
        self.scroll = scroll

        row = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(6))
        self.entry = HudField(hint_text="Transmit a request...")
        self.entry.bind(on_text_validate=self.send)
        listen = NeonButton(text="MIC", size_hint_x=0.16, accent=TEAL, font_size=dp(13))
        listen.bind(on_release=self.listen)
        send = NeonButton(text="ASK", size_hint_x=0.22, font_size=dp(14))
        send.bind(on_release=self.send)
        row.add_widget(self.entry)
        row.add_widget(listen)
        row.add_widget(send)
        root.add_widget(row)
        self.face_panel.set_state("standby")
        return root

    def send(self, *_):
        text = self.entry.text.strip()
        if not text:
            return
        self.entry.text = ""
        self.face_panel.set_state("think")
        self.spoken.text = "Computing..."

        def work():
            result = process_command(text, self.username)
            Clock.schedule_once(lambda *_: self._show_result(text, result), 0)

        threading.Thread(target=work, daemon=True).start()

    def _type_out(self, text):
        if self._type_event is not None:
            self._type_event.cancel()
        self.spoken.text = ""
        chars = list(text or "")

        def step(_dt):
            if not chars:
                self._type_event = None
                return False
            chunk = "".join(chars[:3])
            del chars[:3]
            self.spoken.text += chunk
            return True

        self._type_event = Clock.schedule_interval(step, 0.018)

    def _show_result(self, text, result):
        answer = result.get("text", "")
        self._type_out(answer)
        self.log.text += f"[b]YOU[/b]  {text}\n[b]CORE[/b]  {answer}\n\n"
        self.scroll.scroll_y = 0
        if result.get("url"):
            self.pending_url = result["url"]
            self.pending_source = result.get("source", "Source")
            self.log.text += f"[ref=source][u]Open {self.pending_source}[/u][/ref]\n\n"
            self.log.bind(on_ref_press=self.open_source)

        if result.get("image"):
            self.last_image_path = result["image"]
            self.show_image_popup(self.last_image_path, answer)

        if did_avatar.has_did_key():
            self.face_panel.set_state("think")

            def work():
                try:
                    video_path = did_avatar.generate_talk(answer)
                except Exception as exc:
                    Clock.schedule_once(lambda *_: self._fallback_speak(answer, str(exc)), 0)
                    return
                Clock.schedule_once(lambda *_: self.face_panel.play_talk_video(video_path), 0)

            threading.Thread(target=work, daemon=True).start()
        else:
            self._fallback_speak(answer)

    def _fallback_speak(self, answer, error=None):
        if error:
            self.log.text += f"[i]Avatar video failed, using voice only. ({error})[/i]\n\n"
        self.face_panel.set_state("speak")
        speak(answer, self.voice_profile)
        Clock.schedule_once(lambda *_: self.face_panel.set_state("standby"), min(8, 1.6 + len(answer) / 18))

    def open_source(self, *_):
        if self.pending_url:
            webbrowser.open(self.pending_url)

    def listen(self, *_):
        if not voice_input.is_available():
            self.spoken.text = (
                "Voice input needs a phone, or `pip install SpeechRecognition pyaudio` "
                "for desktop testing."
            )
            return
        self.spoken.text = "Listening..."
        self.face_panel.set_state("listen")

        def on_result(text):
            def apply(*_):
                self.face_panel.set_state("standby")
                self.entry.text = text
                self.send()
            Clock.schedule_once(apply, 0)

        def on_error(msg):
            def apply(*_):
                self.face_panel.set_state("standby")
                self.spoken.text = f"Did not catch that. ({msg})"
            Clock.schedule_once(apply, 0)

        voice_input.listen(on_result, on_error)

    def cloud_popup(self, *_):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        box.add_widget(
            self.label(
                "Paste a Groq API key from console.groq.com.\n"
                "A parent or teacher should create the key. Do not share it.",
                14,
            )
        )
        key_input = HudField(
            hint_text="Paste Groq API key",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(48),
        )
        status = self.label(key_status(), 14)

        def save(*_):
            save_api_key(key_input.text)
            key_input.text = ""
            status.text = key_status()
            if has_api_key():
                speak("Cloud brain connected.", self.voice_profile)

        def clear(*_):
            save_api_key("")
            status.text = key_status()

        box.add_widget(key_input)
        box.add_widget(self.tint_button("Save key", save, height=44))
        box.add_widget(self.tint_button("Remove key", clear, height=44))
        box.add_widget(status)
        styled_popup("CLOUD UPLINK", box, size_hint=(0.94, 0.72))

    def avatar_popup(self, *_):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        box.add_widget(
            self.label(
                "Paste a D-ID API key from studio.d-id.com to make the face "
                "speak with a real animated video. Each reply uses render "
                "minutes on your D-ID plan.",
                14,
            )
        )
        key_input = HudField(
            hint_text="Paste D-ID API key",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(48),
        )
        status = self.label(did_avatar.did_status(), 14)

        def save(*_):
            did_avatar.save_did_key(key_input.text)
            key_input.text = ""
            status.text = did_avatar.did_status()

        def clear(*_):
            did_avatar.save_did_key("")
            status.text = did_avatar.did_status()

        box.add_widget(key_input)
        box.add_widget(self.tint_button("Save key", save, height=44))
        box.add_widget(self.tint_button("Remove key", clear, height=44))
        box.add_widget(status)
        styled_popup("AVATAR CORE", box, size_hint=(0.94, 0.78))

    def show_image_popup(self, path, caption=""):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        box.add_widget(
            Image(source=path, allow_stretch=True, keep_ratio=True, size_hint_y=0.85, nocache=True)
        )
        box.add_widget(self.label(caption or os.path.basename(path), 13))
        close = self.tint_button("Close", lambda *_: popup.dismiss(), height=44)
        box.add_widget(close)
        popup = styled_popup("IMAGE FORGE", box, size_hint=(0.94, 0.9))

    def _add_picture_source_row(self, inner, path_input, status_label=None):
        """Adds a 'Browse for a picture...' + 'Take a photo' button row that
        both fill the given TextInput with a chosen/captured file path."""

        def browse(*_):
            chooser_box = BoxLayout(orientation="vertical", padding=dp(6), spacing=dp(6))
            start_path = os.path.dirname(self.last_image_path) if self.last_image_path else os.path.expanduser("~")
            chooser = FileChooserIconView(path=start_path, filters=["*.png", "*.jpg", "*.jpeg", "*.webp"])
            chooser_box.add_widget(chooser)

            def pick(*_):
                if chooser.selection:
                    path_input.text = chooser.selection[0]
                chooser_popup.dismiss()

            btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
            btn_row.add_widget(self.tint_button("Choose", pick, height=46))
            btn_row.add_widget(self.tint_button("Cancel", lambda *_: chooser_popup.dismiss(), height=46))
            chooser_box.add_widget(btn_row)
            chooser_popup = Popup(title="SELECT VISUAL", content=chooser_box, size_hint=(0.94, 0.9))
            chooser_popup.open()

        def take_photo(*_):
            if not camera_input.is_available():
                if status_label:
                    status_label.text = "Camera is not available on this device."
                return
            if status_label:
                status_label.text = "Opening camera..."

            def on_done(path):
                def apply(*_):
                    path_input.text = path
                    if status_label:
                        status_label.text = "Photo captured."
                Clock.schedule_once(apply, 0)

            def on_error(msg):
                def apply(*_):
                    if status_label:
                        status_label.text = f"Camera: {msg}"
                Clock.schedule_once(apply, 0)

            camera_input.capture(on_done, on_error)

        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        row.add_widget(self.tint_button("Browse for a picture...", browse, height=44))
        row.add_widget(self.tint_button("Take a photo", take_photo, height=44))
        inner.add_widget(row)

    def image_popup(self, *_):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        scroll = ScrollView(size_hint=(1, 1))
        inner = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=dp(4))
        inner.bind(minimum_height=inner.setter("height"))

        inner.add_widget(
            self.label(
                "Paste an OpenAI API key from platform.openai.com/api-keys to draw "
                "and edit pictures. A parent or teacher should create the key. "
                "Every picture uses that account's credits.",
                14,
            )
        )
        key_input = HudField(
            hint_text="Paste OpenAI API key", password=True, multiline=False,
            size_hint_y=None, height=dp(48),
        )
        key_status_lbl = self.label(image_ai.image_status(), 13)

        def save_key(*_):
            image_ai.save_image_key(key_input.text)
            key_input.text = ""
            key_status_lbl.text = image_ai.image_status()

        def clear_key(*_):
            image_ai.save_image_key("")
            key_status_lbl.text = image_ai.image_status()

        inner.add_widget(key_input)
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        row.add_widget(self.tint_button("Save key", save_key, height=44))
        row.add_widget(self.tint_button("Remove key", clear_key, height=44))
        inner.add_widget(row)
        inner.add_widget(key_status_lbl)

        inner.add_widget(self.label("[b]Draw a new picture[/b]", 15))
        gen_prompt = HudField(
            hint_text="Describe the picture, e.g. a red bicycle in a park",
            multiline=False, size_hint_y=None, height=dp(48),
        )
        gen_status = self.label("", 13)
        inner.add_widget(gen_prompt)

        def do_generate(*_):
            prompt = gen_prompt.text.strip()
            if not image_ai.has_image_key():
                gen_status.text = "Add and save an API key first."
                return
            if not prompt:
                gen_status.text = "Describe the picture first."
                return
            gen_status.text = "Drawing..."

            def work():
                try:
                    path = image_ai.generate_image(prompt)
                except Exception as exc:
                    Clock.schedule_once(lambda *_: setattr(gen_status, "text", f"Failed: {exc}"), 0)
                    return

                def done(*_):
                    self.last_image_path = path
                    memory = load_memory()
                    memory["_last_image"] = path
                    save_memory(memory)
                    gen_status.text = "Done."
                    self.show_image_popup(path, prompt)

                Clock.schedule_once(done, 0)

            threading.Thread(target=work, daemon=True).start()

        inner.add_widget(self.tint_button("Generate new image", do_generate, height=46))

        inner.add_widget(self.label("[b]Edit a picture[/b]", 15))
        path_input = HudField(
            hint_text="Picture to edit (tap Browse, or type a file path)",
            multiline=False, size_hint_y=None, height=dp(48),
        )
        if self.last_image_path:
            path_input.text = self.last_image_path
        inner.add_widget(path_input)
        self._add_picture_source_row(inner, path_input)

        edit_prompt = HudField(
            hint_text="Describe the change, e.g. add a birthday hat",
            multiline=False, size_hint_y=None, height=dp(48),
        )
        edit_status = self.label("", 13)
        inner.add_widget(edit_prompt)

        def do_edit(*_):
            source = path_input.text.strip()
            prompt = edit_prompt.text.strip()
            if not image_ai.has_image_key():
                edit_status.text = "Add and save an API key first."
                return
            if not source or not os.path.exists(source):
                edit_status.text = "Pick a picture that exists first."
                return
            if not prompt:
                edit_status.text = "Describe the change first."
                return
            edit_status.text = "Editing..."

            def work():
                try:
                    path = image_ai.edit_image(source, prompt)
                except Exception as exc:
                    Clock.schedule_once(lambda *_: setattr(edit_status, "text", f"Failed: {exc}"), 0)
                    return

                def done(*_):
                    self.last_image_path = path
                    path_input.text = path
                    memory = load_memory()
                    memory["_last_image"] = path
                    save_memory(memory)
                    edit_status.text = "Done."
                    self.show_image_popup(path, prompt)

                Clock.schedule_once(done, 0)

            threading.Thread(target=work, daemon=True).start()

        inner.add_widget(self.tint_button("Edit picture", do_edit, height=46))
        inner.add_widget(edit_status)

        inner.add_widget(self.label("[b]Ask about a picture[/b]", 15))
        ask_path_input = HudField(
            hint_text="Picture to ask about (tap Browse, or type a file path)",
            multiline=False, size_hint_y=None, height=dp(48),
        )
        inner.add_widget(ask_path_input)
        self._add_picture_source_row(inner, ask_path_input)

        question_input = HudField(
            hint_text="What do you want to know about it?",
            multiline=False, size_hint_y=None, height=dp(48),
        )
        ask_status = self.label("", 13)
        inner.add_widget(question_input)

        def do_ask(*_):
            source = ask_path_input.text.strip()
            question = question_input.text.strip()
            if not has_api_key():
                ask_status.text = "Add a Groq or Gemini API key under Cloud first."
                return
            if not source or not os.path.exists(source):
                ask_status.text = "Pick a picture that exists first."
                return
            if not question:
                ask_status.text = "Ask a question about the picture first."
                return
            ask_status.text = "Looking..."

            def work():
                try:
                    answer = ask_cloud_about_image(question, source, self.username)
                except Exception as exc:
                    Clock.schedule_once(lambda *_: setattr(ask_status, "text", f"Failed: {exc}"), 0)
                    return
                Clock.schedule_once(lambda *_: setattr(ask_status, "text", answer), 0)

            threading.Thread(target=work, daemon=True).start()

        inner.add_widget(self.tint_button("Ask about this picture", do_ask, height=46))
        ask_status.text_size = (Window.width - dp(50), None)
        ask_status.size_hint_y = None
        ask_status.bind(texture_size=lambda inst, val: setattr(inst, "height", val[1] + dp(10)))
        inner.add_widget(ask_status)

        scroll.add_widget(inner)
        box.add_widget(scroll)
        box.add_widget(self.tint_button("Close", lambda *_: popup.dismiss(), height=44))
        popup = styled_popup("IMAGE FORGE", box, size_hint=(0.94, 0.94))

    def search_popup(self, *_):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        box.add_widget(
            self.label(
                "Paste a Tavily API key from app.tavily.com to search the web and "
                "get a short summarized answer with sources.",
                14,
            )
        )
        key_input = HudField(
            hint_text="Paste Tavily API key", password=True, multiline=False,
            size_hint_y=None, height=dp(48),
        )
        status = self.label(web_search.search_status(), 14)

        def save(*_):
            web_search.save_search_key(key_input.text)
            key_input.text = ""
            status.text = web_search.search_status()

        def clear(*_):
            web_search.save_search_key("")
            status.text = web_search.search_status()

        box.add_widget(key_input)
        box.add_widget(self.tint_button("Save key", save, height=44))
        box.add_widget(self.tint_button("Remove key", clear, height=44))
        box.add_widget(status)
        box.add_widget(
            self.label("Then just type things like: search for the water cycle", 13)
        )
        styled_popup("SEARCH NET", box, size_hint=(0.94, 0.72))

    def docs_popup(self, *_):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        box.add_widget(
            self.label(
                "Pick a .txt, .md, or .pdf file. Then ask things like: "
                "about the document: what is the main idea? or say "
                "summarize the document. Needs a Groq or Gemini key under Cloud "
                "to answer questions.",
                14,
            )
        )
        current = document_ai.current_document()
        status = self.label(
            f"Loaded: {current['name']}" if current else "No document loaded.", 14
        )
        path_input = HudField(
            hint_text="Tap Browse, or type a file path", multiline=False,
            size_hint_y=None, height=dp(48),
        )

        def browse(*_):
            chooser_box = BoxLayout(orientation="vertical", padding=dp(6), spacing=dp(6))
            chooser = FileChooserIconView(
                path=os.path.expanduser("~"), filters=["*.txt", "*.md", "*.pdf"]
            )
            chooser_box.add_widget(chooser)

            def pick(*_):
                if chooser.selection:
                    path_input.text = chooser.selection[0]
                chooser_popup.dismiss()

            btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
            btn_row.add_widget(self.tint_button("Choose", pick, height=46))
            btn_row.add_widget(self.tint_button("Cancel", lambda *_: chooser_popup.dismiss(), height=46))
            chooser_box.add_widget(btn_row)
            chooser_popup = Popup(title="SELECT FILE", content=chooser_box, size_hint=(0.94, 0.9))
            chooser_popup.open()

        def do_load(*_):
            path = path_input.text.strip()
            if not path or not os.path.exists(path):
                status.text = "Pick a file that exists first."
                return
            status.text = "Reading..."

            def work():
                try:
                    name, words, note = document_ai.load_document(path)
                except Exception as exc:
                    Clock.schedule_once(lambda *_: setattr(status, "text", f"Failed: {exc}"), 0)
                    return

                def done(*_):
                    text = f"Loaded {name} ({words} words)."
                    if note:
                        text += f" {note}"
                    status.text = text

                Clock.schedule_once(done, 0)

            threading.Thread(target=work, daemon=True).start()

        def do_clear(*_):
            document_ai.clear_document()
            status.text = "No document loaded."
            path_input.text = ""

        box.add_widget(path_input)
        box.add_widget(self.tint_button("Browse for a file...", browse, height=44))
        box.add_widget(self.tint_button("Load document", do_load, height=44))
        box.add_widget(self.tint_button("Clear document", do_clear, height=44))
        box.add_widget(status)
        styled_popup("DOC SCANNER", box, size_hint=(0.94, 0.82))

    def voice_popup(self, *_):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        box.add_widget(
            self.label(
                "Choose a built-in assistant voice.\nQuantum Mind cannot copy a real person's voice.",
                14,
            )
        )
        status = self.label(f"Current: {VOICE_PROFILES[self.voice_profile]['label']}", 14)

        def pick(key):
            def _inner(*_):
                self.voice_profile = key
                status.text = f"Current: {VOICE_PROFILES[key]['label']}"
                speak(VOICE_PROFILES[key]["intro"], key)

            return _inner

        for key, data in VOICE_PROFILES.items():
            box.add_widget(self.tint_button(data["label"], pick(key), height=44))
        box.add_widget(status)
        styled_popup("VOICE MATRIX", box, size_hint=(0.92, 0.72))

    def admin_popup(self, *_):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        info = self.label("Add a user account", 16)
        u = HudField(hint_text="Username", multiline=False)
        p = HudField(hint_text="Password", password=True, multiline=False)
        r = HudField(hint_text="Role: student / teacher / admin", multiline=False)
        status = self.label("", 13)

        def save(*_):
            name = u.text.strip().lower()
            role = r.text.strip().lower()
            if not name or not p.text or role not in ("student", "teacher", "admin", "user"):
                status.text = "Enter username, password and a valid role."
                return
            users = load_users()
            users[name] = {"password": hash_pass(p.text), "role": role}
            save_users(users)
            status.text = f"{name} saved as {role}."

        add = self.tint_button("Add / Update User", save, height=48)
        for w in (info, u, p, r, add, status):
            box.add_widget(w)
        styled_popup("ADMIN CONSOLE", box, size_hint=(0.92, 0.75))

    def on_stop(self):
        # Talking-avatar clips are temporary and safe to wipe on exit.
        # Generated/edited pictures are kept in image_cache/ since the
        # user may want to look at or reuse them later.
        stop_speaking()
        did_avatar.clear_cache()


if __name__ == "__main__":
    QMApp().run()
