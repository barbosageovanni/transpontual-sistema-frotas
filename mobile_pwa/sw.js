const CACHE = "tp-checklist-v1";
const ASSETS = [
  "/index.html",
  "/manifest.webmanifest",
  "/icons/icon-192.png",
  "/icons/icon-512.png"
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
});

self.addEventListener("fetch", (e) => {
  const { request } = e;
  const isGET = request.method === "GET";
  const isAPI = request.url.includes("/checklist/") || request.url.includes("/metrics/");
  if (!isGET || isAPI) return; // não cacheia API (sempre on-line)
  e.respondWith(
    caches.match(request).then(cached =>
      cached || fetch(request).then(resp => {
        const copy = resp.clone();
        caches.open(CACHE).then(c => c.put(request, copy));
        return resp;
      }).catch(() => cached)
    )
  );
});
