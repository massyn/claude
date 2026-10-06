---
name: flask-pwa
description: Turn a Flask app into an installable, phone-first Progressive Web App — web app manifest, home-screen and maskable icons, a root-scoped service worker, bottom tab bar navigation, safe-area handling for notched phones, 44px touch targets, bottom-sheet modals, sticky action bars, native share and toast feedback. Builds on the flask skill and deploys unchanged with flask-deploy. Use whenever making a Flask app installable or "app-like", adding a manifest/service worker/offline support/app icons, designing mobile navigation (bottom nav, tab bar) or mobile UI for a Flask app — even if the user doesn't say "PWA" explicitly.
---

# Flask PWA

A PWA layer on top of the `flask` skill's golden template. Everything is served by Flask itself —
no build step, no Node toolchain — so the app still deploys with flask-deploy as-is. Apply the `flask`
and `python` skills as well. Patterns come from Kickstand (`~/github/kickstand`), which runs this setup
in production.

## Adding PWA support to an app

1. Copy `assets/` into the project (it mirrors the project layout): `app/pwa.py`, `app/icons.py`,
   `static/`, `templates/partials/`, `tests/test_pwa.py`. Rename `app.` imports to the project package.
2. Wire the app factory and `base.html` as in `references/wiring.md`.
3. Edit `static/manifest.json` (name, short name, description, colours) and the theme-color meta in
   `templates/partials/pwa_head.html` to match.
4. Design the icon and render the PNG set — `references/icons.md`.
5. Set the tabs in `templates/partials/tab_bar.html` and the section mapping in `app/pwa.py`.
6. Set `PRECACHE` in `static/sw.js` to pages that render signed-out without redirecting.
7. Run `pytest tests/test_pwa.py`.

## Hard rules

- **Service worker at the site root.** Serve `sw.js` from the `/sw.js` route in `app/pwa.py`, never
  from `/static/` — a worker's scope is the path it is served from, so under `/static/` it controls no
  pages. Register it via `static/js/pwa.js` with the URL from `url_for` (no inline script).
- **Service worker handles same-origin GETs only.** Cross-origin requests (Bootstrap CDN, map tiles,
  analytics) routed through the worker are checked against CSP `connect-src` instead of
  `script-src`/`img-src` and get blocked. Never intercept POSTs.
- **Network first.** Pages are server-rendered and must be fresh; the cache is only an offline fallback.
  Bump `CACHE` in `sw.js` whenever `PRECACHE` changes.
- **Bottom tab bar below `lg`, top navbar from `lg` up.** Three to five tabs, each icon + one-word label,
  current tab marked with `active` and `aria-current="page"`. Remove the navbar toggler — no hamburger.
  The active tab comes from `nav_section()` in Python, not template logic.
- **Safe areas.** `viewport-fit=cover` in the viewport meta, and pad anything fixed to the bottom with
  `env(safe-area-inset-bottom)`.
- **Touch targets at least 44px**; form inputs at `1rem` so iOS does not zoom on focus.
- **Icons:** a full manifest set (192, 512, 512 maskable), a 180px `apple-touch-icon`, an SVG favicon and
  a 32px PNG fallback. UI icons are inline SVG strokes from `app/icons.py` — no icon fonts or icon CDNs.
- **Self-host fonts** in `static/fonts/` (with their licence file): offline use, and the CSP keeps
  `font-src 'self'`.
- **No `window.confirm()`** — embedded and installed browsers can block it, silently cancelling the form.
  Use `data-confirm` with `confirm.js`.

## Reference files

| File | Read when |
|------|-----------|
| `references/wiring.md` | Adding the PWA layer to an app — app factory and `base.html` changes |
| `references/icons.md` | Designing the app icon or favicon, rendering the PNGs, the iOS icon cache |
| `references/mobile-ui.md` | Tab bar, icons, sheets, action bars, chips, share/toast, confirm, standalone mode, colours |
| `references/service-worker.md` | Caching, offline behaviour, updates, CSP interaction, deployment |

## Assets

| Path | Purpose |
|------|---------|
| `assets/app/pwa.py` | Blueprint serving `/sw.js`; `nav_section()` and the tab mapping |
| `assets/app/icons.py` | Stroke icon paths (24px grid) — tab, navigation and action icons |
| `assets/static/manifest.json` | Web app manifest |
| `assets/static/sw.js` | Network-first service worker with precached offline fallback |
| `assets/static/css/pwa.css` | Tab bar, safe areas, touch targets, sheets, action bar, chips, toast |
| `assets/static/js/pwa.js` | Service worker registration |
| `assets/static/js/share.js` | Native share sheet with copy-link fallback and `pwaToast()` |
| `assets/static/js/confirm.js` | `data-confirm` forms through a Bootstrap modal |
| `assets/static/icons/` | Starter icon set rendered from `assets/icon-src/` |
| `assets/icon-src/` | Starter `icon.svg` (full-bleed app icon) and `favicon.svg` |
| `assets/templates/partials/` | `pwa_head.html`, `tab_bar.html`, `icons.html` macro, `confirm_modal.html` |
| `assets/tests/test_pwa.py` | Worker scope, precache, manifest, icons, head tags, active tab |
| `scripts/render_icons.py` | Renders the PNG icon set from the two SVGs with headless Chrome/Edge |
