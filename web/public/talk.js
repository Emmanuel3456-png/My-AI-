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
  item.className = "bubble-row " + role;
  if (role === "bot") {
    item.innerHTML = '<img class="logo" src="/assets/core.jpg" alt="" /><div class="bubble"></div>';
  } else {
    item.innerHTML = '<div class="bubble"></div>';
  }
  item.querySelector(".bubble").textContent = text;
  log.appendChild(item);
  log.scrollTop = log.scrollHeight;
}
async function send(text) {
  if (!text) return;
  add("user", text);
  add("bot", "Thinking…");
  const pending = log.lastElementChild.querySelector(".bubble");
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });
    const reply = data.reply || data.error || "No reply.";
    pending.textContent = reply;
    if (data.image) {
      const pic = document.createElement("img");
      pic.src = data.image;
      pic.style.maxWidth = "220px";
      pic.style.borderRadius = "8px";
      pic.style.marginTop = "8px";
      pending.appendChild(pic);
    }
    speak(reply);
  } catch (_) {
    pending.textContent = "Core busy. Wait a few seconds.";
  }
}
form.addEventListener("submit", (e) => {
  e.preventDefault();
  const t = input.value.trim();
  input.value = "";
  send(t);
});
const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
if (Speech) {
  const rec = new Speech();
  rec.lang = "en-US";
  mic.onclick = () => { rec.start(); mic.textContent = "Listening"; };
  rec.onresult = (e) => { mic.textContent = "Mic"; send(e.results[0][0].transcript); };
  rec.onend = () => { mic.textContent = "Mic"; };
}
add("bot", "Quantum Mind is ready. Created by Emmanuel Abraham.");
fetch("/api/chat-status").then(r => r.json()).then(d => {
  statusEl.textContent = d.ready ? "Cloud core online." : "Cloud core waiting.";
}).catch(() => {});
