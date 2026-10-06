// Network first; when offline, fall back to a precached copy of the page.
// Bump CACHE whenever PRECACHE changes so the activate step drops the old copies.
const CACHE = 'app-v1';
// Pages that render without signing in and without redirecting. A URL that redirects (for
// example '/' sending signed-in users elsewhere) caches the redirect, not a page.
const PRECACHE = ['/about'];

self.addEventListener('install', e =>
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(PRECACHE)))
);

self.addEventListener('activate', e =>
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))))
);

// Only our own GETs have a cached copy to fall back to. Leave writes and cross-origin requests
// (CDN, map tiles, analytics) to the browser: fetched from here they would be checked against the
// CSP's connect-src instead of script-src/img-src, and blocked.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET' || new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
});
