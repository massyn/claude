# App icons and favicons

## The set

| File | Size | Background | Used by |
|------|------|------------|---------|
| `static/icons/favicon.svg` | vector | transparent | Browser tab (`<link rel="icon" type="image/svg+xml">`) |
| `static/icons/favicon-32.png` | 32×32 | transparent | Favicon fallback |
| `static/icons/apple-touch-icon.png` | 180×180 | solid | iPhone/iPad home screen |
| `static/icons/icon-192.png` | 192×192 | solid | Manifest, `purpose: any` |
| `static/icons/icon-512.png` | 512×512 | solid | Manifest, `purpose: any` **and** a separate `purpose: maskable` entry |

One 512 file serves both purposes when the artwork sits inside the maskable safe zone (below).

## Two source SVGs

Keep the sources in the project (e.g. `design/icon.svg`, `design/favicon.svg`); the starter pair is in
`assets/icon-src/`.

- **`icon.svg` — the app icon.** A full-bleed 512×512 square with a solid background colour (the
  manifest's `background_color` reads well). No transparency and no rounded corners — iOS and Android
  apply their own masks. Keep all artwork within a circle of radius 204.8 around the centre (the 80%
  maskable safe zone); Android may crop to a circle, squircle or teardrop anywhere outside it.
- **`favicon.svg` — the mark alone** on a transparent background, drawn bolder and simpler than the app
  icon so it still reads at 16–32px: thicker strokes, fewer details, no text.

Design guidance that worked for Kickstand's badge:

- One recognisable shape in the brand accent colour, on the app's dark ground. Flat paths only — no
  gradients, shadows or outlined text, which turn to mush at small sizes.
- A ring or rounded container around the mark gives a consistent silhouette across platform masks.
- Keep a horizontal lockup (mark + wordmark, text outlined) as a separate SVG for the navbar brand.
- Test it small: render the 32px favicon and look at it before committing.

## Rendering the PNGs

```bash
python <skill>/scripts/render_icons.py --icon design/icon.svg --favicon design/favicon.svg --out static/icons
```

It drives headless Chrome or Edge (auto-detected; `--browser` or `CHROME_PATH` to override), writes the
four PNGs and copies `favicon.svg` into place. Run it once when the artwork changes and commit the PNGs —
nothing renders at build or deploy time. Look at the outputs before committing.

## Head tags and manifest

`templates/partials/pwa_head.html` links the favicon pair, the apple-touch-icon and the manifest, and sets
`theme-color`. Keep `theme-color` in the partial and `theme_color` in `manifest.json` the same — it tints
the Android status bar and the installed app's title bar.

## Changing an icon later

- **iOS snapshots the home-screen icon when it is added.** After a new icon deploys, remove the
  home-screen shortcut and add it again; no cache-busting fixes this.
- Android and desktop Chrome refresh the installed icon from the manifest on their own schedule (can be a
  day or more).
- Browsers cache favicons aggressively; a hard refresh or a new filename forces it.
