const express = require("express");
const path = require("path");

const app = express();
const publicDir = path.join(__dirname, "..", "public");

app.use(express.json());
app.use(express.static(publicDir, { extensions: ["html"] }));

app.get("/api/health", (_req, res) => {
  res.json({
    name: "Quantum Mind",
    status: "online",
    purpose: "general-assistant",
    illegalFeatures: false,
  });
});

app.get("/api/release", (_req, res) => {
  res.json({
    version: "3.0",
    apk: "/downloads/QuantumMind-3.0.apk",
    notes: "General assistant build. No hacking tools included.",
  });
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Quantum Mind site on ${port}`);
});
