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
  return item.querySelector(".bubble");
}

async function send(text) {
  if (!text) return;
  add("user", text);
  const pending = add("bot", "Thinking…");
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();
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
  } catch (err) {
    pending.textContent = "Core busy. Wait a few seconds.";
  }
}

form.addEventListener("submit", function (event) {
  event.preventDefault();
  const text = input.value.trim();
  input.value = "";
  send(text);
});

const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
if (Speech && mic) {
  const rec = new Speech();
  rec.lang = "en-US";
  mic.addEventListener("click", function () {
    window.speechSynthesis.cancel();
    rec.start();
    mic.textContent = "Listening";
  });
  rec.onresult = function (event) {
    mic.textContent = "Mic";
    send(event.results[0][0].transcript);
  };
  rec.onend = function () {
    mic.textContent = "Mic";
  };
}

add("bot", "Quantum Mind is ready. Created by Emmanuel Abraham. Type or tap Mic.");
fetch("/api/chat-status")
  .then(function (res) { return res.json(); })
  .then(function (data) {
    statusEl.textContent = data.ready ? "Cloud core online." : "Cloud core waiting.";
  })
  .catch(function () {
    statusEl.textContent = "Core unreachable.";
  });
