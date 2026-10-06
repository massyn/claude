# Service worker

## What `static/sw.js` does

- **install** — opens cache `CACHE` and stores every URL in `PRECACHE`.
- **activate** — deletes caches with any other name, so bumping `CACHE` clears old copies.
- **fetch** — for same-origin GETs only: try the network, and if it fails return the cached copy. Every
  other request is left to the browser untouched.

Only `PRECACHE` URLs have a cached copy; other pages show the browser's offline error. That is
deliberate for server-rendered apps where stale data is worse than none.

## Rules

- **Root scope.** The worker controls only URLs under the path it is served from, so `app/pwa.py` serves
  it at `/sw.js`. Kickstand first served it from `/static/sw.js`, where it controlled no pages. If an app
  ever registered a worker from another path, unregister that registration once:

  ```js
  const oldScope = new URL('/static/', location.href).href;
  navigator.serviceWorker.getRegistrations().then(regs =>
    regs.filter(r => r.scope === oldScope).forEach(r => r.unregister()));
  ```

- **Same-origin GETs only.** A request the worker re-issues with `fetch()` is checked against CSP
  `connect-src`. CDN scripts, map tiles and analytics are allowed under `script-src`/`img-src`, not
  `connect-src`, so intercepting them gets them blocked. Writes (POST) must always go straight to the
  server.
- **Precache only pages that return 200 signed out.** `addAll` stores whatever the URL returns; a URL
  that redirects (a `/` that forwards signed-in users, anything behind `login_required`) stores the
  redirect. `test_precached_pages_render_without_redirect` checks this.
- **Never cache personal pages** in the worker. Cache storage outlives the session, so on a shared device
  the next person would see them offline.

## Updates

- The browser re-fetches `/sw.js` on navigation and installs a new worker when the file's bytes change.
  Bump `CACHE` whenever `PRECACHE` changes.
- Flask serves the file with conditional caching (ETag) by default; don't add a long `Cache-Control`
  to `/sw.js` or updates stall.
- The new worker waits until every tab of the app is closed before taking over. That is fine for a
  network-first worker; if a change must apply immediately, add `self.skipWaiting()` in install and
  `clients.claim()` in activate.

## Extending offline support

If the app needs more than a static fallback (e.g. "last viewed" pages), cache successful same-origin
navigations at runtime inside the fetch handler (`response.ok` and `response.type === 'basic'`), and clear
the cache on logout (`caches.delete(CACHE)` from the logout page's script). Keep personal data out unless
the app is single-user.

## Deployment with flask-deploy

Nothing changes: `/sw.js` and `/static/...` are ordinary Flask responses behind Nginx. Service workers
require HTTPS (localhost is exempt), which Cloudflare or `--ssl` already provides. Installability needs
HTTPS, a manifest with name, icons 192/512, `start_url` and `display`, and a registered worker.
