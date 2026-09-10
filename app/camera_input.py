"""Camera capture for Quantum Mind.

Lets a student take a photo directly instead of only picking one that
already exists in storage. Uses plyer's camera facade, which launches the
phone's own camera app and hands the saved file back - Quantum Mind never
gets raw camera access itself.

On desktop (no camera facade available) this reports itself unavailable
so the UI can fall back to "Browse for a picture" only.
"""
from __future__ import annotations

import os
import time

CAMERA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "camera_cache")


def is_available() -> bool:
    try:
        from plyer import camera  # noqa: F401

        return True
    except Exception:
        return False


def capture(on_complete, on_error=None):
    """Opens the native camera app. Calls on_complete(path) when a photo is
    saved, or on_error(msg) if the camera isn't available or was cancelled."""
    try:
        from plyer import camera
    except Exception as exc:
        if on_error:
            on_error(f"Camera is not available on this device. ({exc})")
        return

    os.makedirs(CAMERA_DIR, exist_ok=True)
    path = os.path.join(CAMERA_DIR, f"photo_{int(time.time())}.jpg")

    def _finished(*args):
        # plyer's on_complete callback shape has varied across versions;
        # the safest check is simply whether a file showed up.
        if os.path.exists(path) and os.path.getsize(path) > 0:
            on_complete(path)
        elif on_error:
            on_error("No photo was saved. The camera may have been cancelled.")

    try:
        camera.take_picture(filename=path, on_complete=_finished)
    except NotImplementedError as exc:
        if on_error:
            on_error(f"Camera is not supported on this platform. ({exc})")
    except Exception as exc:
        if on_error:
            on_error(str(exc))


def clear_cache():
    if not os.path.isdir(CAMERA_DIR):
        return
    for name in os.listdir(CAMERA_DIR):
        try:
            os.remove(os.path.join(CAMERA_DIR, name))
        except OSError:
            pass
