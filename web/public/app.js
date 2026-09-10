async function checkApk() {
  const link = document.getElementById("apk-link");
  const status = document.getElementById("apk-status");
  if (!link || !status) return;
  try {
    const res = await fetch(link.getAttribute("href"), { method: "HEAD" });
    if (!res.ok) throw new Error("missing");
    status.textContent = "Ready for Android. Chrome will download the file.";
  } catch (_) {
    link.classList.add("disabled");
    link.textContent = "APK not uploaded yet";
    status.textContent = "After you build the APK, put it in public/downloads/QuantumMind-3.0.apk and redeploy.";
  }
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}

checkApk();
