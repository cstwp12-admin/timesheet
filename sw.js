/* Offline use: network first (so updates arrive), cached copy when there is no signal.
   Bump the version after changing files so phones fetch the new ones. */
const C = "ts-v0.9.7";
const PRE = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png",
  "lib/jspdf.umd.min.js", "lib/jszip.min.js", "lib/pdf-lib.min.js", "lib/qrcode.min.js", "lib/jsQR.min.js", "lib/pdfjs.min.js", "lib/pdfjs.worker.min.js",
  "app-data.js", "templates/form.xlsx", "templates/form.layout.json", "templates/logo.jpeg",
  "packages/index.json", "packages/WP11.json", "packages/WP12.json", "packages/WP13.json", "packages/WP14.json", "packages/OTHER.json",
  "holidays/SABAH.json"];
self.addEventListener("install", e => { e.waitUntil(caches.open(C).then(c => c.addAll(PRE)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => x !== C).map(x => caches.delete(x)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const r = e.request; if (r.method !== "GET") return;
  const u = new URL(r.url);
  const ok = u.origin === location.origin || /fonts\.(googleapis|gstatic)\.com$/.test(u.hostname);
  if (!ok) return;
  e.respondWith(fetch(r).then(res => { if (res.ok) { const cp = res.clone(); caches.open(C).then(c => c.put(r, cp)); } return res; })
    .catch(() => caches.match(r, { ignoreSearch: true }).then(m => m || caches.match("index.html"))));
});
