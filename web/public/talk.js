const log = document.getElementById("log");
const form = document.getElementById("ask");
const input = document.getElementById("q");
const statusEl = document.getElementById("key-status");

function speak(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 1;
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

async function checkStatus() {
  try {
    const res = await fetch("/api/chat-status");
    const data = await res.json();
    statusEl.textContent = data.ready ? "Cloud core online." : "Cloud core waiting.";
  } catch (_) {
    statusEl.textContent = "Core unreachable.";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
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
    pending.querySelector("p").textContent = "Could not reach the core.";
  }
});

add("bot", "Quantum Mind is ready. Ask anything legal and appropriate.");
checkStatus();
