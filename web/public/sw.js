self.addEventListener("install", (event) => {
  event.waitUntil(caches.open("qm-v1").then((cache) => cache.addAll(["/", "/styles.css", "/app.js"])));
});
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((hit) => hit || fetch(event.request))
  );
});
