const log = document.getElementById("log");
const form = document.getElementById("ask");
const input = document.getElementById("q");
const statusEl = document.getElementById("key-status");
const mic = document.getElementById("mic");
const menu = document.getElementById("menu");
const scrim = document.getElementById("scrim");
const menuBtn = document.getElementById("menuBtn");
const modeBtn = document.getElementById("modeBtn");
const hints = document.getElementById("hints");
const projectsEl = document.getElementById("projects");
const camBtn = document.getElementById("camBtn");
const fileBtn = document.getElementById("fileBtn");
const camInput = document.getElementById("camInput");
const fileInput = document.getElementById("fileInput");
let mode = "general";
let voiceOn = true;
let attached = "";
const HINTS = [
  "Who created Quantum Mind?",
  "Explain gravity in simple words",
  "Help me plan a study timetable",
  "Search the latest news about space",
  "Write a short Python hello program"
];
let hintI = 0;

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
  let extra = text;
  if (attached) extra += "\n\n" + attached;
  if (mode === "coding") return "Coding mode.\n" + extra;
  if (mode === "study") return "Study mode. Explain step by step.\n" + extra;
  return extra;
}
async function send(text) {
  if (!text && !attached) return;
  add("user", text || "Sent an attachment.");
  const pending = add("bot", "Thinking…");
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: packed(text || "Please look at the attached file.") })
    });
    const data = await res.json();
    pending.textContent = data.reply || data.error || "No reply.";
    if (data.image) {
      const pic = document.createElement("img");
      pic.src = data.image;
      pic.style.maxWidth = "180px";
      pic.style.borderRadius = "8px";
      pic.style.marginTop = "8px";
      pending.appendChild(pic);
    }
    speak(pending.textContent);
  } catch (err) {
    pending.textContent = "Core busy. Wait a few seconds.";
  }
  attached = "";
}
function closeMenu() { menu.hidden = true; scrim.hidden = true; }
form.addEventListener("submit", function (e) {
  e.preventDefault();
  const text = input.value.trim();
  input.value = "";
  send(text);
});
menuBtn.addEventListener("click", function () {
  menu.hidden = !menu.hidden;
  scrim.hidden = menu.hidden;
});
modeBtn.addEventListener("click", function () {
  mode = mode === "general" ? "study" : mode === "study" ? "coding" : "general";
  modeBtn.textContent = mode === "coding" ? "</>" : mode === "study" ? "▣" : "◈";
});
scrim.addEventListener("click", closeMenu);
menu.addEventListener("click", function (event) {
  const btn = event.target.closest("button");
  if (!btn) return;
  if (btn.dataset.mode) { mode = btn.dataset.mode; closeMenu(); }
  if (btn.dataset.act === "new") {
    log.innerHTML = "";
    add("bot", "New chat. Created by Emmanuel Abraham.");
    closeMenu();
  }
  if (btn.dataset.act === "video") {
    add("bot", "Starting video…");
    fetch("/api/video", { method: "POST" })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d.url) window.open(d.url, "_blank");
        else add("bot", d.error || "Video did not start.");
      })
      .catch(function () { add("bot", "Video did not start."); });
    closeMenu();
  }
  if (btn.dataset.act === "voice") {
    voiceOn = !voiceOn;
    btn.textContent = voiceOn ? "Voice on" : "Voice off";
  }
  if (btn.dataset.act === "project") {
    const name = window.prompt("Project name");
    if (!name) return;
    const list = JSON.parse(localStorage.getItem("qmProjects") || "[]");
    list.push(name);
    localStorage.setItem("qmProjects", JSON.stringify(list));
    projectsEl.innerHTML += '<div class="project-item">' + name + "</div>";
  }
});
camBtn.addEventListener("click", function () { camInput.click(); });
fileBtn.addEventListener("click", function () { fileInput.click(); });
function readFile(file) {
  if (!file) return;
  if (file.type.indexOf("image/") === 0) {
    const reader = new FileReader();
    reader.onload = function () {
      const box = add("user", "Photo: " + file.name);
      const pic = document.createElement("img");
      pic.src = reader.result;
      pic.style.maxWidth = "180px";
      pic.style.borderRadius = "10px";
      pic.style.marginTop = "8px";
      box.appendChild(pic);
      attached = "The user attached a photo called " + file.name + ".";
    };
    reader.readAsDataURL(file);
    return;
  }
  add("user", "File: " + file.name);
  const reader = new FileReader();
  reader.onload = function () { attached = String(reader.result).slice(0, 4000); };
  reader.readAsText(file);
}
camInput.addEventListener("change", function () { readFile(camInput.files[0]); });
fileInput.addEventListener("change", function () { readFile(fileInput.files[0]); });
const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
if (Speech && mic) {
  const rec = new Speech();
  rec.lang = "en-US";
  mic.addEventListener("click", function () {
    window.speechSynthesis.cancel();
    rec.start();
  });
  rec.onresult = function (event) { send(event.results[0][0].transcript); };
}
setInterval(function () {
  hints.textContent = HINTS[hintI % HINTS.length];
  hintI += 1;
}, 3500);
hints.textContent = HINTS[0];
add("bot", "Quantum Mind is ready. Created by Emmanuel Abraham.");
fetch("/api/chat-status").then(function (r) { return r.json(); }).then(function (d) {
  statusEl.textContent = d.ready ? "Cloud core online." : "Cloud core waiting.";
}).catch(function () { statusEl.textContent = "Core unreachable."; });
