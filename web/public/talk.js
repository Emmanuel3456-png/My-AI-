const log = document.getElementById("log");
const form = document.getElementById("ask");
const input = document.getElementById("q");
const statusEl = document.getElementById("key-status");
const mic = document.getElementById("mic");

function speak(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  window.speechSynthesis.speak(u);
}
function add(role, text) {
  const item = document.createElement("article");
  item.className = "msg " + role;
  item.innerHTML = "<strong>" + (role === "user" ? "You" : "Quantum Mind") + "</strong><p></p>";
  item.querySelector("p").textContent = text;
  log.appendChild(item);
  log.scrollTop = log.scrollHeight;
}
async function send(text) {
  if (!text) return;
  add("user", text);
  add("bot", "Thinking…");
  const pending = log.lastElementChild;
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();
    const reply = data.reply || data.error || "No reply.";
    pending.querySelector("p").textContent = reply;
    speak(reply);
  } catch (_) {
    pending.querySelector("p").textContent = "Core busy. Wait 10 seconds if the free server was asleep.";
  }
}
form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  input.value = "";
  send(text);
});
const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
if (Speech) {
  const rec = new Speech();
  rec.lang = "en-US";
  mic.onclick = () => { rec.start(); mic.textContent = "Listening"; };
  rec.onresult = (e) => { mic.textContent = "Mic"; send(e.results[0][0].transcript); };
  rec.onend = () => { mic.textContent = "Mic"; };
} else {
  mic.disabled = true;
}
add("bot", "Quantum Mind is ready. Created by Emmanuel Abraham. Type or tap Mic.");
fetch("/api/chat-status").then(r => r.json()).then(d => {
  statusEl.textContent = d.ready ? "Cloud core online." : "Cloud core waiting.";
}).catch(() => { statusEl.textContent = "Core unreachable."; });
