# Start building Quantum Mind

Do this in order. Phone (Termux) can do steps 1–3. The APK needs a Linux computer for step 4.

## Step 1 — GitHub repo

1. Open https://github.com and sign in.
2. New repository.
3. Name it `QuantumMind`.
4. Leave it empty (no README).
5. Create a personal access token: GitHub → Settings → Developer settings → Personal access tokens.

On the machine that has this folder:

```bash
cd QuantumMind
git init
git add .
git commit -m "Quantum Mind public start"
git branch -M main
git remote add origin https://github.com/YOUR_USER/QuantumMind.git
git push -u origin main
```

On Termux first run:

```bash
pkg update
pkg install git
```

When GitHub asks for a password, paste the token.

## Step 2 — Put the website on Render

1. Open https://render.com and sign in with GitHub.
2. New → Web Service.
3. Select the `QuantumMind` repo.
4. Settings:
   - Root directory: `web`
   - Runtime: Node
   - Build command: `npm install`
   - Start command: `npm start`
5. Deploy.
6. Copy the `onrender.com` URL.
7. Open that URL in Chrome. That is your public site.

The Download button stays off until an APK file exists.

## Step 3 — Groq key (can be on your phone)

1. Open https://console.groq.com/keys
2. Create an API key.
3. Keep it private.
4. After the app is installed, tap CLOUD and paste it.

## Step 4 — Build the APK (Linux computer)

Termux cannot reliably build this APK.

```bash
pip install buildozer
cd app
buildozer android debug
cp bin/*.apk ../web/public/downloads/QuantumMind-3.0.apk
cd ..
git add web/public/downloads/QuantumMind-3.0.apk
git commit -m "Add Android APK"
git push
```

Render will redeploy. Then Chrome on a phone can download and install it.

## Step 5 — Open it on your phone

1. Chrome → your Render URL
2. Download APK
3. Allow install from Chrome
4. Open Quantum Mind
5. Continue as guest, or create an account
6. Paste the Groq key under CLOUD
