const express = require("express");
const path = require("path");
const app = express();
const publicDir = path.join(__dirname, "..", "public");
app.use(express.json());
app.use(express.static(publicDir, { extensions: ["html"] }));

app.get("/api/health", (_req, res) => {
  res.json({ name: "Quantum Mind", status: "online", purpose: "general-assistant" });
});

app.get("/api/chat-status", (_req, res) => {
  res.json({ ready: Boolean(process.env.GROQ_API_KEY) });
});

app.post("/api/chat", async (req, res) => {
  const key = process.env.GROQ_API_KEY;
  const message = String((req.body && req.body.message) || "").trim().slice(0, 2000);
  if (!message) return res.status(400).json({ error: "Type a question first." });
  if (!key) {
    return res.json({
      reply: "The website core is online, but no Groq key is set on the server yet. Add GROQ_API_KEY in Render."
    });
  }
  try {
    const groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: "Bearer " + key,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "llama-3.1-8b-instant",
        temperature: 0.4,
        max_tokens: 500,
        messages: [
          {
            role: "system",
            content: "You are Quantum Mind, a calm general assistant for everyone. Keep answers clear, legal, and family-friendly. Refuse hacking, weapons, crime, and adult topics."
          },
          { role: "user", content: message }
        ]
      })
    });
    const data = await groqRes.json();
    const reply =
      (data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content) ||
      (data.error && data.error.message) ||
      "The cloud core returned no text.";
    res.json({ reply });
  } catch (err) {
    res.status(500).json({ error: "Cloud core failed. Try again in a moment." });
  }
});

app.get("/api/release", (_req, res) => {
  res.json({ version: "3.0", apk: "/downloads/QuantumMind-3.0.apk" });
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log("Quantum Mind site on " + port);
});
