# Templates and UI

## Layout

- `base.html` defines layout, navbar, flash messages and footer; every page extends it and fills
  `{% block content %}` (plus `title`, `extra_css`, `extra_js` as needed).
- Bootstrap 5 via jsDelivr CDN with SRI `integrity` attributes.
- Flash messages render in `base.html`; the `error` category maps to Bootstrap's `danger`.
- Errors (404, 429, 500) render `error.html` via handlers in the app factory.

## Navbar

- Always `sticky-top`, never `fixed-top` (which needs manual body padding).
- Use the `.app-navbar` class (coloured by `theme.css`) instead of Bootstrap's `bg-dark`.
- Use Unicode icons on navbar items — no icon library needed:

| Item | Icon |
|------|------|
| Home | 🏠 |
| About | ℹ️ |
| Login | 🔑 |
| Logout | 🚪 |
| User (dropdown) | 👤 |

- Signed out: a `🔑 Login` link to `auth.login`. Signed in: a dropdown labelled with the user's email
  (falling back to name) containing `🚪 Logout`. See `assets/template/templates/base.html`.

## CSS theming

Two files with separate owners:

| File | Role |
|------|------|
| `static/theme.css` | Palette only — CSS custom properties on `:root` plus the few rules that apply them to `body` and `.app-navbar`. Swapping this file re-themes the site |
| `static/style.css` | Component styling. References theme variables for anything that should follow the palette; hard-codes values only for deliberate one-off choices |

Standard variables (extend the set when an app needs more, e.g. `--color-border`, `--color-surface`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `--color-bg` | `#ffffff` | Body background |
| `--color-fg` | `#212529` | Body text |
| `--color-primary` | `#0d6efd` | Primary accent — buttons, links |
| `--color-navbar` | `#212529` | Navbar background |
| `--color-accent` | `#6c757d` | Secondary accent — badges, secondary buttons |

Load order in `base.html`: Bootstrap → `theme.css` → `style.css` (when the app has one) → `{% block extra_css %}`.

When retrofitting an existing app, extract its current colours into `theme.css` rather than imposing a
new scheme, and change only colour properties in `style.css` — the app should render identically.
Do not add a dark mode unless asked; a full alternative theme is a second file (e.g. `theme-dark.css`)
redefining the same variables.

## Admin list views

- No edit or delete buttons on list rows. The whole row is clickable and opens the detail/edit screen
  (`table-hover`, `cursor: pointer`).
- Delete lives on the detail/edit screen only, behind a Bootstrap modal confirmation (never
  `window.confirm()`), and POSTs to a dedicated `/delete` route.
- Every table is paginated in SQL — never render unbounded lists, never paginate client-side.
  Query params `page` (default 1) and `per_page` (default 25); `LIMIT per_page OFFSET (page-1)*per_page`.
  Render Bootstrap pagination showing current and total pages.
- Every column header is sortable via `sort` and `direction` (`asc`/`desc`) query params. Clicking toggles
  direction; show an arrow for the active sort. Whitelist sort columns in the route — never pass raw
  query params into SQL.

## Version footer

`VERSION` (set at deploy time) is injected by the app factory's context processor. `base.html` renders a
small muted footer only when it is non-empty.

## Google tag

`GTAG_ID` is injected by the same context processor. `base.html` renders the gtag snippet before
Bootstrap only when it is set — no empty script blocks. See `security.md` for the CSP additions it needs.
