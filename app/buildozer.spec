[app]
title = Quantum Mind
package.name = quantummind
package.domain = org.quantummind
source.dir = .
source.filename = Main.py
source.include_exts = py,png,jpg,jpeg,webp,kv,atlas,json,mp3,mp4,txt
version = 3.0.0
# Note: pymupdf (used only for reading scanned/image-only PDF pages) is a
# compiled package. It installs fine with `pip install pymupdf` for running
# on a computer, but it is not guaranteed to build for Android through
# python-for-android - test an Android build before relying on that feature.
requirements = python3==3.11.10,kivy==2.3.0
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,RECORD_AUDIO,CAMERA,READ_EXTERNAL_STORAGE,READ_MEDIA_IMAGES
android.api = 34
android.minapi = 23
android.ndk = 25b
android.buildtools_version = 34.0.0
android.accept_sdk_license = True
android.archs = arm64-v8a
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
