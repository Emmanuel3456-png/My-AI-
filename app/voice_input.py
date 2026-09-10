"""Speech-to-text voice input for Quantum Mind.

Lets a student tap Listen, speak a question out loud, and have it typed
into the entry box automatically. Uses Android's own on-device speech
recognizer through a system dialog - no audio is sent to Quantum Mind's
own servers, no API key is needed, and this cannot listen in the
background: it only activates while the Listen popup is open and stops
right after one answer.

On a desktop (for testing outside a phone) this falls back to Python's
`speech_recognition` package if it happens to be installed, and otherwise
reports that voice input needs a phone.
"""
from __future__ import annotations

_REQUEST_CODE = 1002
_pending_unbind = None


def is_available() -> bool:
    try:
        from jnius import autoclass  # noqa: F401
        from android import activity  # noqa: F401

        return True
    except Exception:
        return _desktop_available()


def _desktop_available() -> bool:
    try:
        import speech_recognition  # noqa: F401

        return True
    except Exception:
        return False


def listen(on_result, on_error=None):
    """Starts one round of listening. Calls on_result(text) or on_error(msg)
    from a background thread/callback - callers should hop back onto the
    Kivy clock before touching widgets."""
    try:
        _listen_android(on_result, on_error)
        return
    except Exception:
        pass
    _listen_desktop(on_result, on_error)


def _listen_android(on_result, on_error):
    from jnius import autoclass
    from android import activity

    global _pending_unbind

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent = autoclass("android.content.Intent")
    RecognizerIntent = autoclass("android.speech.RecognizerIntent")
    Activity = autoclass("android.app.Activity")

    activity_inst = PythonActivity.mActivity
    intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
    intent.putExtra(
        RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
    )
    intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Ask Quantum Mind something...")

    def on_activity_result(request_code, result_code, data):
        if request_code != _REQUEST_CODE:
            return
        try:
            if result_code == Activity.RESULT_OK and data is not None:
                results = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                if results is not None and results.size() > 0:
                    on_result(str(results.get(0)))
                    return
            if on_error:
                on_error("No speech was recognized. Try again.")
        except Exception as exc:
            if on_error:
                on_error(str(exc))
        finally:
            try:
                activity.unbind(on_activity_result=on_activity_result)
            except Exception:
                pass

    _pending_unbind = on_activity_result
    activity.bind(on_activity_result=on_activity_result)
    activity_inst.startActivityForResult(intent, _REQUEST_CODE)


def _listen_desktop(on_result, on_error):
    try:
        import speech_recognition as sr
    except Exception:
        if on_error:
            on_error(
                "Voice input needs a phone with Android speech recognition, "
                "or `pip install SpeechRecognition pyaudio` for desktop testing."
            )
        return

    def work():
        try:
            r = sr.Recognizer()
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.4)
                audio = r.listen(source, timeout=6, phrase_time_limit=12)
            text = r.recognize_google(audio)
            on_result(text)
        except Exception as exc:
            if on_error:
                on_error(str(exc))

    import threading

    threading.Thread(target=work, daemon=True).start()
