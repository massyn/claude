# Phone-first UI

The app is used one-handed, outdoors, often installed. Everything here is in `static/css/pwa.css`,
coloured from `theme.css` variables so it follows the app's palette.

## Navigation: bottom tab bar

- Below Bootstrap's `lg` breakpoint a fixed tab bar (`partials/tab_bar.html`) replaces the navbar links;
  from `lg` up the navbar shows them and the bar is hidden (`d-lg-none`). No hamburger menu.
- Three to five tabs. Each is an icon above a one-word label (`.75rem`, weight 600); the active tab is
  in the primary colour, weight 700, with `aria-current="page"`.
- Tabs are destinations, not actions. Put the account side (profile, help, terms, privacy, admin, log
  out) behind a single **Me** tab rather than spending tabs on them. Signed-out users get a shorter set
  ending in **Sign in**.
- `body` gets bottom padding equal to the bar height plus the safe-area inset, so the page end is never
  hidden behind it.
- When installed on a phone (`@media (display-mode: standalone)`), the footer is hidden — its links live
  on the Me tab.

## Icons

Inline SVG strokes on a 24px grid, `stroke="currentColor"`, width 1.8, round caps and joins — they take
the text colour and stay crisp at any size.

- Paths live in `app/icons.py` (`UI_ICONS`; add app-specific ones to `APP_ICONS`), exposed to templates
  as `icon_paths`. Draw one with the macro: `{% from "partials/icons.html" import icon %}` then
  `{{ icon('share') }}` (22px) or `{{ icon('plus', 'pwa-icon pwa-icon-sm') }}` (18px).
- Page scripts that need icons (e.g. map markers) get the paths passed in from the route, so there is
  one source.
- Pair icons with text. An icon-only button uses `.btn .pwa-icon-btn` (44px square) **and** an
  `aria-label`.
- Domain icons (Kickstand's fuel, coffee, scenic waypoint kinds) are worth drawing in the same style —
  they make lists scannable. Keep emoji for text that leaves the app (WhatsApp messages), not the UI.

## Touch and readability

- Minimum 44px tap targets: `.btn`, inputs and selects get `min-height: 44px`; `.btn-lg` is 56px for the
  page's main action.
- Inputs at `font-size: 1rem` — anything smaller makes iOS zoom the page on focus.
- Muted text at a contrast of about 7:1 against the background for outdoor reading (Kickstand: `#a6a6a6`
  on `#111111`). Bootstrap's default `text-muted` is too faint on dark themes.
- Numbers that line up in columns (times, distances, counts): `font-variant-numeric: tabular-nums`.

## Choosing from a few options: chips

A row of radio buttons styled as tiles beats a `<select>` on a phone:

```html
<div class="pwa-chips" style="grid-template-columns: repeat(3, 1fr)">
  <input type="radio" class="btn-check" name="kind" id="kind-fuel" value="fuel" checked>
  <label class="pwa-chip" for="kind-fuel">{{ icon('pin') }} Fuel</label>
  ...
</div>
```

## Sheets and action bars

- **Bottom sheet:** add `pwa-sheet` to a Bootstrap `.modal`. Below `sm` it slides up from the bottom
  with rounded top corners and clears the home indicator; on wider screens it is a normal modal. Use it
  for pickers and short forms ("add a stop"), and for confirmations.
- **Sticky action bar:** wrap the page's primary actions in `<div class="pwa-action-bar">`. On phones it
  sticks just above the tab bar; from `lg` it sits inline as a bordered card. One primary (`btn-lg`)
  action, the rest outline or icon buttons.

## Share and feedback

- **Share:** `<button data-share-url="{{ url }}" data-share-title="..." data-share-text="...">` opens the
  phone's native share sheet; without one it copies the link and shows a toast. Closing the sheet is not
  an error. `data-share-fallback="id"` clicks another element instead of copying (e.g. a modal with the
  text and an "Open WhatsApp" link).
- **Toast:** `window.pwaToast('Saved')` shows a short pill above the tab bar (`role="status"`), for
  confirmations that need no action.
- **Confirm:** `<form method="post" data-confirm="Delete this trip?">`. The OK button repeats the submit
  button's text and keeps its danger styling. Never `window.confirm()`.

## Theme and fonts

- A dark ground with one accent colour reads well outdoors and makes the installed app feel native. Set
  `data-bs-theme="dark"` on `<html>` and map Bootstrap's variables (`--bs-body-bg`, `--bs-body-color`,
  `--bs-link-color`, `--bs-border-color`) to the `theme.css` palette.
- `theme-color` (meta and manifest) colours the Android status bar; `background_color` is the splash
  screen behind the icon on launch.
- Self-host the brand font as a variable `woff2` in `static/fonts/` with its licence, declare it with
  `font-display: swap`, and `<link rel="preload" as="font" crossorigin>` it in the head.
