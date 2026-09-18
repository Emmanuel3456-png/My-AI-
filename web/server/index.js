const express = require("express");
const path = require("path");
const app = express();
const publicDir = path.join(__dirname, "..", "public");
app.use(express.json());
app.use(express.static(publicDir, { extensions: ["html"] }));

const SYSTEM = "You are Quantum Mind, a calm public AI created by Emmanuel Abraham. If asked who made you or who Emmanuel Abraham is, say Emmanuel Abraham created Quantum Mind. Keep answers clear, legal, and family-friendly. Refuse hacking, weapons, crime, and adult topics.";

app.get("/api/health", (_req, res) => res.json({ name: "Quantum Mind", status: "online" }));
app.get("/api/chat-status", (_req, res) => res.json({
  ready: Boolean(process.env.GROQ_API_KEY),
  search: Boolean(process.env.TAVILY_API_KEY),
  image: Boolean(process.env.OPENAI_API_KEY),
  video: Boolean(process.env.TAVUS_API_KEY)
}));

function wantsSearch(t) { return /\b(search|look up|latest|news|current|who won|what happened|today|find online)\b/i.test(t); }
function wantsImage(t) { return /\b(draw|picture|image|illustration|generate art|make an image)\b/i.test(t); }

app.post("/api/chat", async (req, res) => {
  const key = process.env.GROQ_API_KEY;
  const message = String((req.body && req.body.message) || "").trim().slice(0, 2000);
  if (!message) return res.status(400).json({ error: "Type a question first." });
  if (!key) return res.json({ reply: "Add GROQ_API_KEY in Render." });
  try {
   if (wantsImage(message) && process.env.OPENAI_API_KEY) {
      const imgRes = await fetch("https://api.openai.com/v1/images/generations", {
        method: "POST",
        headers: {
          Authorization: "Bearer " + process.env.OPENAI_API_KEY,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          model: "gpt-image-1",
          prompt: "Family-friendly digital art. " + message,
          size: "512x512",
          n: 1
        })
      });
      const img = await imgRes.json();
      const url = img.data && img.data[0] && img.data[0].url;
      if (url) return res.json({ reply: "Here is an image.", image: url });
      return res.json({
        reply: "Image core said: " + ((img.error && img.error.message) || "no image returned")
      });
    } 
    let extra = "";
    if (wantsSearch(message) && process.env.TAVILY_API_KEY) {
      const sRes = await fetch("https://api.tavily.com/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: process.env.TAVILY_API_KEY, query: message, max_results: 3 })
      });
      const s = await sRes.json();
      extra = ((s.results || []).map(r => (r.title || "") + ": " + (r.content || "")).join("\n")).slice(0, 1200);
    }
    const groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: { Authorization: "Bearer " + key, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "openai/gpt-oss-20b",
        temperature: 0.4,
        max_tokens: 500,
        messages: [
          { role: "system", content: SYSTEM },
          extra ? { role: "system", content: "Web notes:\n" + extra } : null,
          { role: "user", content: message }
        ].filter(Boolean)
      })
    });
    const data = await groqRes.json();
    const reply = (data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content) || (data.error && data.error.message) || "No text.";
    res.json({ reply });
  } catch (e) {
    res.status(500).json({ error: "Cloud core failed." });
  }
});
app.get("/api/release", (_req, res) => res.json({ version: "3.0", apk: "/downloads/QuantumMind-3.0.apk" }));
app.listen(process.env.PORT || 3000, () => console.log("Quantum Mind site up"));
