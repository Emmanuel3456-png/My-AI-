"""Safe on-device speech helpers.

Quantum Mind can speak with a few built-in assistant voices.
It cannot copy or clone a real person's voice.
"""
from __future__ import annotations

import threading

VOICE_PROFILES = {
    "quantum": {
        "label": "Quantum",
        "rate": 1.0,
        "pitch": 1.05,
        "intro": "Quantum voice online.",
    },
    "calm": {
        "label": "Calm Guide",
        "rate": 0.88,
        "pitch": 0.95,
        "intro": "Calm guide voice ready.",
    },
    "bright": {
        "label": "Bright Helper",
        "rate": 1.12,
        "pitch": 1.18,
        "intro": "Bright helper voice ready.",
    },
    "teacher": {
        "label": "Teacher",
        "rate": 0.95,
        "pitch": 1.0,
        "intro": "Teacher voice ready.",
    },
}


def _android_speak(text: str, rate: float, pitch: float) -> bool:
    try:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
        Locale = autoclass("java.util.Locale")
        activity = PythonActivity.mActivity
        tts = getattr(_android_speak, "_tts", None)
        if tts is None:
            tts = TextToSpeech(activity, None)
            tts.setLanguage(Locale.UK)
            _android_speak._tts = tts
        tts.setSpeechRate(float(rate))
        tts.setPitch(float(pitch))
        tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, "quantum-mind")
        return True
    except Exception:
        return False


def _plyer_speak(text: str) -> bool:
    try:
        from plyer import tts

        tts.speak(text)
        return True
    except Exception:
        return False


def speak(text: str, profile: str = "quantum") -> bool:
    """Speak text with a built-in profile. Returns True if audio started."""
    if not text:
        return False
    data = VOICE_PROFILES.get(profile, VOICE_PROFILES["quantum"])
    spoken = str(text)

    def run():
        if not _android_speak(spoken, data["rate"], data["pitch"]):
            _plyer_speak(spoken)

    threading.Thread(target=run, daemon=True).start()
    return True


def stop_speaking() -> None:
    try:
        tts = getattr(_android_speak, "_tts", None)
        if tts is not None:
            tts.stop()
    except Exception:
        pass
