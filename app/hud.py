"""Premium holographic HUD widgets for Quantum Mind."""
from __future__ import annotations

import math
import os
import random
from datetime import datetime

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.video import Video
from kivy.uix.widget import Widget

CYAN = (0.28, 0.94, 1, 1)
CYAN_DIM = (0.14, 0.58, 0.82, 1)
TEAL = (0.08, 0.86, 0.76, 1)
AMBER = (1.0, 0.78, 0.28, 1)
GLOW_TEXT = (0.78, 0.97, 1, 1)
MUTED_TEXT = (0.58, 0.82, 0.94, 1)
BTN_FILL = (0.03, 0.18, 0.34, 0.94)
BTN_FILL_ALT = (0.02, 0.30, 0.28, 0.94)
PANEL = (0.02, 0.06, 0.12, 0.78)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FACE_PATH = os.path.join(BASE_DIR, "gideon_face.jpg")
BG_PATH = os.path.join(BASE_DIR, "hud_bg.jpg")


class NeonButton(Button):
    def __init__(self, text="", accent=None, fill=None, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("color", GLOW_TEXT)
        kwargs.setdefault("bold", True)
        super().__init__(text=text, **kwargs)
        self.accent = accent or CYAN
        self._fill = fill or BTN_FILL
        with self.canvas.before:
            self._fill_color = Color(*self._fill)
            self._bg = RoundedRectangle(radius=[dp(9)] * 4)
            self._glow = Color(self.accent[0], self.accent[1], self.accent[2], 0.18)
            self._halo = Line(width=2.4, rounded_rectangle=(0, 0, 10, 10, dp(9)))
            self._line_color = Color(*self.accent)
            self._border = Line(width=1.15, rounded_rectangle=(0, 0, 10, 10, dp(9)))
        self.bind(pos=self._sync, size=self._sync, state=self._press)
        self._sync()

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        x, y, w, h = self.x, self.y, self.width, self.height
        self._border.rounded_rectangle = (x + 1, y + 1, max(w - 2, 1), max(h - 2, 1), dp(9))
        self._halo.rounded_rectangle = (x - 1, y - 1, max(w + 2, 1), max(h + 2, 1), dp(10))

    def _press(self, *_):
        if self.state == "down":
            self._fill_color.rgba = (0.10, 0.58, 0.78, 1)
        else:
            self._fill_color.rgba = self._fill


class HudField(TextInput):
    def __init__(self, **kwargs):
        kwargs.setdefault("background_color", (0.015, 0.05, 0.10, 0.92))
        kwargs.setdefault("foreground_color", GLOW_TEXT)
        kwargs.setdefault("cursor_color", CYAN)
        kwargs.setdefault("hint_text_color", (0.34, 0.56, 0.72, 1))
        kwargs.setdefault("padding", [dp(14), dp(12), dp(14), dp(12)])
        kwargs.setdefault("multiline", False)
        kwargs.setdefault("selection_color", (0.10, 0.55, 0.75, 0.35))
        super().__init__(**kwargs)


class ScanLine(Widget):
    def __init__(self, speed=0.22, **kwargs):
        super().__init__(**kwargs)
        self.speed = speed
        self._yoff = 0
        with self.canvas:
            Color(0.30, 0.96, 1, 0.16)
            self._wash = Rectangle(size=(10, 10))
            Color(0.45, 0.98, 1, 0.42)
            self._bar = Rectangle(size=(10, dp(2)))
        self.bind(pos=self._place, size=self._place)
        Clock.schedule_interval(self._tick, 1 / 40.0)

    def _place(self, *_):
        self._wash.pos = self.pos
        self._wash.size = (self.width, max(self._yoff, 1))
        self._bar.size = (self.width, dp(2.2))

    def _tick(self, dt):
        if self.height <= 1:
            return
        self._yoff = (self._yoff + self.height * dt * self.speed) % self.height
        self._wash.pos = self.pos
        self._wash.size = (self.width, max(self._yoff * 0.18, 1))
        self._bar.pos = (self.x, self.y + self.height - self._yoff)


class OrbitRing(Widget):
    """Rotating tick ring drawn around the face."""

    def __init__(self, radius_hint=0.42, speed=18, ticks=48, **kwargs):
        super().__init__(**kwargs)
        self.radius_hint = radius_hint
        self.speed = speed
        self.ticks = ticks
        self.angle = random.uniform(0, 360)
        self._lines = []
        with self.canvas:
            self._color = Color(0.30, 0.92, 1, 0.55)
            for _ in range(ticks):
                self._lines.append(Line(width=1.05, points=[0, 0, 1, 1]))
        self.bind(pos=self._redraw, size=self._redraw)
        Clock.schedule_interval(self._spin, 1 / 30.0)

    def _spin(self, dt):
        self.angle = (self.angle + self.speed * dt) % 360
        self._redraw()

    def _redraw(self, *_):
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        radius = min(self.width, self.height) * self.radius_hint
        for i, line in enumerate(self._lines):
            a = math.radians(self.angle + i * (360 / self.ticks))
            inner = radius * (0.92 if i % 4 else 0.84)
            outer = radius
            line.points = [
                cx + inner * math.cos(a),
                cy + inner * math.sin(a),
                cx + outer * math.cos(a),
                cy + outer * math.sin(a),
            ]


class ParticleField(Widget):
    def __init__(self, count=28, **kwargs):
        super().__init__(**kwargs)
        self.dots = []
        with self.canvas:
            for _ in range(count):
                color = Color(0.35, 0.9, 1, random.uniform(0.12, 0.45))
                blob = Ellipse(size=(dp(2), dp(2)), pos=(0, 0))
                self.dots.append(
                    {
                        "color": color,
                        "blob": blob,
                        "x": random.random(),
                        "y": random.random(),
                        "s": random.uniform(0.015, 0.045),
                        "size": random.uniform(1.4, 3.2),
                    }
                )
        Clock.schedule_interval(self._drift, 1 / 30.0)

    def _drift(self, dt):
        for d in self.dots:
            d["y"] = (d["y"] + d["s"] * dt) % 1.0
            d["x"] = (d["x"] + math.sin(d["y"] * 8) * 0.01 * dt) % 1.0
            sz = dp(d["size"])
            d["blob"].size = (sz, sz)
            d["blob"].pos = (self.x + d["x"] * self.width, self.y + d["y"] * self.height)


class FramePanel(Widget):
    """Rounded panel with corner brackets used behind logs and replies."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*PANEL)
            self._bg = RoundedRectangle(radius=[dp(12)] * 4)
            Color(*CYAN)
            self._frame = Line(width=1.05, rounded_rectangle=(0, 0, 10, 10, dp(12)))
            Color(0.35, 0.95, 1, 0.9)
            self._tl = Line(width=1.5)
            self._tr = Line(width=1.5)
            self._bl = Line(width=1.5)
            self._br = Line(width=1.5)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        x, y, w, h = self.x, self.y, self.width, self.height
        self._frame.rounded_rectangle = (x + 1, y + 1, max(w - 2, 1), max(h - 2, 1), dp(12))
        arm = min(dp(16), w * 0.08, h * 0.22)
        p = dp(7)
        self._tl.points = [x + p, y + h - p - arm, x + p, y + h - p, x + p + arm, y + h - p]
        self._tr.points = [x + w - p - arm, y + h - p, x + w - p, y + h - p, x + w - p, y + h - p - arm]
        self._bl.points = [x + p, y + p + arm, x + p, y + p, x + p + arm, y + p]
        self._br.points = [x + w - p - arm, y + p, x + w - p, y + p, x + w - p, y + p + arm]


class FacePanel(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.01, 0.04, 0.08, 0.55)
            self._panel = RoundedRectangle(radius=[dp(16)] * 4)
            Color(*CYAN)
            self._frame = Line(width=1.2, rounded_rectangle=(0, 0, 10, 10, dp(16)))
            Color(0.35, 0.95, 1, 0.95)
            self._tl = Line(width=1.7)
            self._tr = Line(width=1.7)
            self._bl = Line(width=1.7)
            self._br = Line(width=1.7)
        self.bind(pos=self._draw_hud, size=self._draw_hud)

        self.face = Image(
            source=FACE_PATH,
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(0.78, 0.86),
            pos_hint={"center_x": 0.5, "center_y": 0.54},
            opacity=0.98,
        )
        self.ring_a = OrbitRing(radius_hint=0.46, speed=14, ticks=52, size_hint=(1, 1))
        self.ring_b = OrbitRing(radius_hint=0.38, speed=-22, ticks=36, size_hint=(1, 1))
        self.scan = ScanLine(size_hint=(0.62, 0.72), pos_hint={"center_x": 0.5, "center_y": 0.54})
        self.video = None
        self.status = Label(
            text="STANDBY",
            font_size=dp(13),
            color=CYAN,
            bold=True,
            size_hint=(1, None),
            height=dp(26),
            pos_hint={"center_x": 0.5, "y": 0.015},
        )
        self.add_widget(self.face)
        self.add_widget(self.ring_a)
        self.add_widget(self.ring_b)
        self.add_widget(self.scan)
        self.add_widget(self.status)
        self._pulse = None
        self.state_name = "standby"
        self.set_state("standby")

    def _draw_hud(self, *_):
        self._panel.pos = self.pos
        self._panel.size = self.size
        x, y, w, h = self.x, self.y, self.width, self.height
        self._frame.rounded_rectangle = (x + 2, y + 2, max(w - 4, 1), max(h - 4, 1), dp(16))
        arm = min(dp(24), w * 0.08, h * 0.12)
        p = dp(10)
        self._tl.points = [x + p, y + h - p - arm, x + p, y + h - p, x + p + arm, y + h - p]
        self._tr.points = [x + w - p - arm, y + h - p, x + w - p, y + h - p, x + w - p, y + h - p - arm]
        self._bl.points = [x + p, y + p + arm, x + p, y + p, x + p + arm, y + p]
        self._br.points = [x + w - p - arm, y + p, x + w - p, y + p, x + w - p, y + p + arm]

    def set_state(self, state):
        labels = {
            "standby": "◈  CORE ONLINE  •  STANDBY  ◈",
            "listen": "◈  AUDIO UPLINK  •  LISTENING  ◈",
            "think": "◈  QUANTUM CORE  •  COMPUTING  ◈",
            "speak": "◈  VOICE CHANNEL  •  TRANSMITTING  ◈",
            "boot": "◈  SYSTEMS  •  INITIALIZING  ◈",
        }
        self.state_name = state
        self.status.text = labels.get(state, "QUANTUM MIND")
        if state == "listen":
            self.status.color = TEAL
            self.ring_a.speed = 36
            self.ring_b.speed = -48
        elif state == "think":
            self.status.color = AMBER
            self.ring_a.speed = 48
            self.ring_b.speed = -62
        elif state == "speak":
            self.status.color = CYAN
            self.ring_a.speed = 28
            self.ring_b.speed = -34
        else:
            self.status.color = CYAN
            self.ring_a.speed = 14
            self.ring_b.speed = -22
        if self._pulse is not None:
            self._pulse.cancel()
            self._pulse = None
        if state in ("listen", "speak", "think", "boot"):
            self._dir = 1
            self._pulse = Clock.schedule_interval(self._animate, 0.04)
        else:
            self.face.opacity = 0.98

    def _animate(self, dt):
        self.face.opacity += 0.016 * getattr(self, "_dir", 1)
        if self.face.opacity >= 1:
            self._dir = -1
        elif self.face.opacity <= 0.78:
            self._dir = 1

    def play_talk_video(self, video_path, on_finish=None):
        if self._pulse is not None:
            self._pulse.cancel()
            self._pulse = None
        self.face.opacity = 1
        for w in (self.face, self.scan):
            if w.parent:
                self.remove_widget(w)
        if self.video is not None:
            self.remove_widget(self.video)
        self.video = Video(
            source=video_path,
            state="play",
            options={"allow_stretch": True, "keep_ratio": True},
            size_hint=(0.78, 0.86),
            pos_hint={"center_x": 0.5, "center_y": 0.54},
        )

        def _back_to_face(*_):
            if self.video is not None:
                self.video.state = "stop"
                self.remove_widget(self.video)
            self.add_widget(self.face)
            self.add_widget(self.scan)
            self.add_widget(self.status)
            self.set_state("standby")
            if on_finish:
                on_finish()

        self.video.bind(eos=_back_to_face)
        self.add_widget(self.video)
        self.add_widget(self.status)
        self.set_state("speak")


class Stage(FloatLayout):
    """Full-window stage with cinematic background + particles."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bg = Image(source=BG_PATH, allow_stretch=True, keep_ratio=False)
        self.particles = ParticleField()
        self.content = FloatLayout()
        self.add_widget(self.bg)
        self.add_widget(self.particles)
        self.add_widget(self.content)
        self.bg.bind(size=self._fit, pos=self._fit)
        self.bind(size=self._fit, pos=self._fit)

    def _fit(self, *_):
        for w in (self.bg, self.particles, self.content):
            w.pos = self.pos
            w.size = self.size

    def set_content(self, widget):
        self.content.clear_widgets()
        widget.size_hint = (1, 1)
        widget.pos_hint = {"x": 0, "y": 0}
        self.content.add_widget(widget)


class ClockLabel(Label):
    def __init__(self, **kwargs):
        kwargs.setdefault("font_size", dp(12))
        kwargs.setdefault("color", MUTED_TEXT)
        kwargs.setdefault("halign", "right")
        kwargs.setdefault("valign", "middle")
        super().__init__(**kwargs)
        Clock.schedule_interval(self._tick, 1)
        self._tick(0)

    def _tick(self, _dt):
        self.text = datetime.now().strftime("%H:%M:%S  •  %d %b %Y")


def styled_popup(title, content, size_hint=(0.94, 0.76)):
    popup = Popup(
        title=f"  {title}  ",
        content=content,
        size_hint=size_hint,
        title_color=CYAN,
        title_size=dp(16),
        separator_color=CYAN_DIM,
        separator_height=dp(1.5),
        background_color=(0.02, 0.07, 0.12, 1),
        auto_dismiss=True,
    )
    popup.open()
    return popup


def glow_label(text, size=16, color=None):
    return Label(
        text=text,
        font_size=dp(size),
        color=color or GLOW_TEXT,
        markup=True,
        halign="center",
        valign="middle",
    )
