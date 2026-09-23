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
const plusBtn = document.getElementById("plusBtn");
const plusMenu = document.getElementById("plusMenu");
const camInput = document.getElementById("camInput");
const galInput = document.getElementById("galInput");
const fileInput = document.getElementById("fileInput");
let mode = "general";
let voiceOn = true;
let attached = "";
const HINTS = [
  "Who created Quantum Mind?",
  "Write a Python file that prints hello",
  "Explain gravity in simple words",
  "Search the latest news about space",
  "Help me plan a study timetable"
];
let hintI = 0;

function clean(text) {
  return String(text)
    .replace(/\*\*/g, "")
    .replace(/###/g, "")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/\|/g, " ")
    .replace(/-{3,}/g, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}
function speak(text) {
  if (!voiceOn || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));
}
function fadeRows() {
  const rows = log.querySelectorAll(".bubble-row");
  rows.forEach(function (row, i) {
    const dist = rows.length - 1 - i;
    row.style.opacity = dist === 0 ? "1" : dist === 1 ? "0.72" : dist === 2 ? "0.42" : "0.18";
  });
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
  fadeRows();
  return item.querySelector(".bubble");
}
function packed(text) {
  let extra = text;
  if (attached) extra += "\n\n" + attached;
  extra += "\n\nReply in short plain sentences. No markdown tables. If you write code, include the full file.";
  if (mode === "coding") return "Coding mode. Write a complete small file.\n" + extra;
  if (mode === "study") return "Study mode. Explain simply.\n" + extra;
  return extra;
}
function addDownload(box, raw) {
  const looksLikeCode = mode === "coding" || /```/.test(raw) || /\b(def |function |print\(|#include|const |let )/i.test(raw);
  if (!looksLikeCode) return;
  const code = String(raw).replace(/```[a-z]*\n?/gi, "").replace(/```/g, "").trim();
  const name = /\bhtml\b|\.html\b/i.test(raw) ? "quantum-mind.html" : /\bpython\b|\.py\b|print\(/i.test(raw) ? "quantum-mind.py" : "quantum-mind.txt";
  const link = document.createElement("a");
  link.className = "dl";
  link.textContent = "Download " + name;
  link.download = name;
  link.href = URL.createObjectURL(new Blob([code], { type: "text/plain" }));
  box.appendChild(link);
}
function closePlus() {
  plusMenu.hidden = true;
  plusBtn.textContent = "+";
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
    const raw = data.reply || data.error || "No reply.";
    pending.textContent = clean(raw);
    addDownload(pending, raw);
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
  closePlus();
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
plusBtn.addEventListener("click", function () {
  plusMenu.hidden = !plusMenu.hidden;
  plusBtn.textContent = plusMenu.hidden ? "+" : "×";
});
document.getElementById("camBtn").addEventListener("click", function () { closePlus(); camInput.click(); });
document.getElementById("galBtn").addEventListener("click", function () { closePlus(); galInput.click(); });
document.getElementById("fileBtn").addEventListener("click", function () { closePlus(); fileInput.click(); });
menu.addEventListener("click", function (event) {
  const btn = event.target.closest("button");
  if (!btn) return;
  if (btn.dataset.mode) { mode = btn.dataset.mode; closeMenu(); }
  if (btn.dataset.act === "new") {
    log.innerHTML = "";
    add("bot", "New chat. Created by Emmanuel Abraham.");
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
function showPhoto(name, dataUrl) {
  const box = add("user", "Photo: " + name);
  const pic = document.createElement("img");
  pic.src = dataUrl;
  pic.style.maxWidth = "180px";
  pic.style.borderRadius = "10px";
  pic.style.marginTop = "8px";
  box.appendChild(pic);
  attached = "The user attached a photo called " + name + ".";
}
function shrinkImage(file) {
  const reader = new FileReader();
  reader.onload = function () {
    const img = new Image();
    img.onload = function () {
      const scale = Math.min(800 / img.width, 800 / img.height, 1);
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(img.width * scale));
      canvas.height = Math.max(1, Math.round(img.height * scale));
      canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
      showPhoto(file.name, canvas.toDataURL("image/jpeg", 0.7));
    };
    img.src = reader.result;
  };
  reader.readAsDataURL(file);
}
function readFile(file) {
  if (!file) return;
  if (file.type.indexOf("image/") === 0) { shrinkImage(file); return; }
  add("user", "File: " + file.name);
  const reader = new FileReader();
  reader.onload = function () { attached = String(reader.result).slice(0, 4000); };
  reader.readAsText(file);
}
camInput.addEventListener("change", function () { readFile(camInput.files[0]); });
galInput.addEventListener("change", function () { readFile(galInput.files[0]); });
fileInput.addEventListener("change", function () { readFile(fileInput.files[0]); });
const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
if (Speech && mic) {
  const rec = new Speech();
  rec.lang = "en-US";
  mic.addEventListener("click", function () {
    closePlus();
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
