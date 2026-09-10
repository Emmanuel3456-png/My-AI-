# Quantum Mind — website + APK (public general-assistant build)

This is the clean path to put Quantum Mind on the public internet so people can open the site in Chrome and download the Android APK.

This project will not include hacking, cracking, bypassing locks, breaking into accounts, or any other illegal access. Those features will not be added.

## What each tool is for

| Tool | Use it for | Do not use it for |
|---|---|---|
| GitHub | Store the website and the Kivy app | Secret API keys or student passwords |
| Render | Host the website so Chrome can open it | Building the Android APK |
| Termux | Git commands from an Android phone | Compiling a full Kivy APK (too heavy) |
| Buildozer on Linux | Build the Kivy APK | — |
| EAS (Expo) | Expo / React Native apps only | This Kivy app. EAS cannot build Quantum Mind |

Quantum Mind is Python + Kivy. Expo EAS will not package it. Use Buildozer.

Chrome also does not have an “APK store.” People:
1. Open your Render URL in Chrome
2. Tap Download APK
3. Install the file on Android

## Folder plan (two GitHub repos is simplest)

1. `quantum-mind-app` — the Kivy project (`Main.py`, `hud.py`, …)
2. `quantum-mind-web` — this website

You can keep both in one repo if you prefer. Render should start from the website folder.

## 1. Put the website on GitHub (computer or Termux)

On a computer:

```bash
cd quantum-mind-web
git init
git add .
git commit -m "Quantum Mind website"
```

Create an empty GitHub repository, then:

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USER/quantum-mind-web.git
git push -u origin main
```

From Termux:

```bash
pkg update
pkg install git
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
# copy the website folder onto the phone, then the same git commands
```

Use a GitHub personal access token when it asks for a password.

## 2. Host it on Render

1. Sign in at https://render.com
2. New + Web Service
3. Connect the GitHub repo
4. Render will read `render.yaml`
5. If you set it manually:
   - Runtime: Node
   - Build: `npm install`
   - Start: `npm start`
6. Deploy
7. Open the `onrender.com` URL in Chrome

That URL is the public site. You can later attach a custom domain in Render.

## 3. Build the APK (Linux, not Termux)

On a Linux computer or a Linux cloud machine:

```bash
pip install buildozer
cd "Quantum Mind"
buildozer android debug
```

The APK appears under `bin/`. Rename it:

```bash
cp bin/*.apk ../quantum-mind-web/public/downloads/QuantumMind-3.0.apk
```

Commit and push the website repo again. Render will redeploy. The Download button turns on.

Building a Kivy APK can take a long time the first run. Test the finished APK on one phone before you share the link.

## 4. What “frontend and backend 100%” means here

Already built:
- Frontend for the phone app: Kivy HUD in `Main.py` + `hud.py`
- Frontend for the public site: this folder
- App “backend”: optional accounts, memory files, and optional cloud keys
- Site backend: `/api/health` and `/api/release` on Render

Not included, on purpose:
- Hacking modules
- Silent access to other people’s phones or accounts
- A claim that this is the best AI in the world — it is a general assistant that uses keys you provide

If you want a larger backend later, the legal next step is a public account API that stores memory and settings — not network intrusion.

## 5. Safety before you go public

- Change the default `admin` / `admin123` login
- Never put Groq, Gemini, OpenAI, Tavily, or D-ID keys in GitHub
- Do not publish real student names or passwords
- State that the APK is an independent app, not an official Google or OpenAI product
