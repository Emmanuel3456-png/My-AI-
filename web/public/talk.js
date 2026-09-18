const log = document.getElementById("log");
const form = document.getElementById("ask");
const input = document.getElementById("q");
const statusEl = document.getElementById("key-status");
const mic = document.getElementById("mic");
const menu = document.getElementById("menu");
const scrim = document.getElementById("scrim");
const menuBtn = document.getElementById("menuBtn");
const modeTag = document.getElementById("modeTag");
const hints = document.getElementById("hints");
const projectsEl = document.getElementById("projects");
let mode = "general";
let voiceOn = true;
const HINTS = [
  "Who created Quantum Mind?",
  "Explain gravity in simple words",
  "Help me plan a study timetable",
  "Search the latest news about space",
  "Write a short Python hello program",
  "What is a neural network?"
];

function speak(text) {
  if (!voiceOn || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));
}
function add(role, text) {
  const item = document.createElement("article");
  item.className = "bubble-row " + role;
  item.innerHTML = role === "bot"
    ? '<img class="logo" src="/assets/core.jpg" alt="" /><div class="bubble"></div>'
    : '<div class="bubble"></div>';
  item.querySelector(".bubble").textContent = text;
  log.appendChild(item);
  log.scrollTop = log.scrollHeight;
  return item.querySelector(".bubble");
}
function packed(text) {
  if (mode === "coding") return "Coding mode. Give a short, clear program or explanation.\n" + text;
  if (mode === "study") return "Study mode. Explain step by step for a student.\n" + text;
  return text;
}
async function send(text) {
  if (!text) return;
  add("user", text);
  const pending = add("bot", "Thinking…");
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: packed(text) })
    });
    const data = await res.json();
    const reply = data.reply || data.error || "No reply.";
    pending.textContent = reply;
    speak(reply);
  } catch (err) {
    pending.textContent = "Core busy. Wait a few seconds.";
  }
}
function closeMenu() { menu.hidden = true; scrim.hidden = true; }
function setMode(next) {
  mode = next;
  modeTag.textContent = next === "coding" ? "Coding" : next === "study" ? "Study" : "General";
  closeMenu();
}
function renderProjects() {
  const list = JSON.parse(localStorage.getItem("qmProjects") || "[]");
  projectsEl.innerHTML = "";
  list.forEach(function (name) {
    const row = document.createElement("div");
    row.className = "project-item";
    row.textContent = name;
    projectsEl.appendChild(row);
  });
}
form.addEventListener("submit", function (event) {
  event.preventDefault();
  const text = input.value.trim();
  input.value = "";
  send(text);
});
menuBtn.addEventListener("click", function () {
  menu.hidden = !menu.hidden;
  scrim.hidden = menu.hidden;
});
scrim.addEventListener("click", closeMenu);
menu.addEventListener("click", function (event) {
  const btn = event.target.closest("button");
  if (!btn) return;
  if (btn.dataset.mode) setMode(btn.dataset.mode);
  if (btn.dataset.act === "new") {
    log.innerHTML = "";
    add("bot", "New chat. Created by Emmanuel Abraham.");
    closeMenu();
  }
  if (btn.dataset.act === "voice") {
    voiceOn = !voiceOn;
    btn.textContent = voiceOn ? "Voice on" : "Voice off";
    if (!voiceOn) window.speechSynthesis.cancel();
  }
  if (btn.dataset.act === "project") {
    const name = window.prompt("Project name");
    if (!name) return;
    const list = JSON.parse(localStorage.getItem("qmProjects") || "[]");
    list.push(name);
    localStorage.setItem("qmProjects", JSON.stringify(list));
    renderProjects();
  }
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
  rec.onend = function () { mic.textContent = "Mic"; };
}
HINTS.forEach(function (text, i) {
  const el = document.createElement("div");
  el.className = "hint";
  el.textContent = text;
  el.style.animationDelay = (i * 7) + "s";
  hints.appendChild(el);
});
renderProjects();
add("bot", "Quantum Mind is ready. Created by Emmanuel Abraham.");
fetch("/api/chat-status").then(function (res) { return res.json(); }).then(function (data) {
  statusEl.textContent = data.ready ? "Cloud core online." : "Cloud core waiting.";
}).catch(function () { statusEl.textContent = "Core unreachable."; });
