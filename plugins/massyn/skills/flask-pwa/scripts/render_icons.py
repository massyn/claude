"""Render a PWA's PNG icon set from two SVGs with a headless Chromium browser (Chrome or Edge).

    python render_icons.py --icon icon.svg --favicon favicon.svg --out static/icons

--icon     full-bleed square app icon (solid background, artwork inside the central 80% circle so the
           maskable crop never cuts it) -> apple-touch-icon.png (180), icon-192.png, icon-512.png
--favicon  mark on a transparent background -> favicon-32.png, and copied as favicon.svg

Run once when the artwork changes and commit the PNGs; no rasteriser is needed at build or deploy time.
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

ICON_SIZES = {"apple-touch-icon.png": 180, "icon-192.png": 192, "icon-512.png": 512}
FAVICON_SIZES = {"favicon-32.png": 32}

BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome",
    "chromium",
    "chromium-browser",
    "microsoft-edge",
]


class RenderError(RuntimeError):
    pass


def find_browser(explicit: str | None) -> str:
    for candidate in [explicit, os.environ.get("CHROME_PATH"), *BROWSER_CANDIDATES]:
        if not candidate:
            continue
        resolved = shutil.which(candidate) or (
            candidate if Path(candidate).is_file() else None
        )
        if resolved:
            return resolved
    raise RenderError("No Chrome/Edge found. Pass --browser or set CHROME_PATH.")


def render(browser: str, svg: Path, size: int, out: Path, workdir: Path) -> None:
    # Wrap the SVG in a page exactly size×size so the screenshot is the icon and nothing else.
    page = workdir / f"{out.stem}.html"
    page.write_text(
        '<!doctype html><html><body style="margin:0;background:transparent">'
        f'<img src="{svg.resolve().as_uri()}" width="{size}" height="{size}" style="display:block">'
        "</body></html>",
        encoding="utf-8",
    )
    command = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        "--default-background-color=00000000",
        f"--window-size={size},{size}",
        f"--screenshot={out.resolve()}",
        page.resolve().as_uri(),
    ]
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=60, check=False
    )
    if result.returncode != 0 or not out.is_file():
        raise RenderError(f"Rendering {out.name} failed: {result.stderr.strip()}")
    logger.info("Wrote %s (%dx%d)", out, size, size)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--icon", type=Path, required=True, help="Full-bleed square app icon SVG"
    )
    parser.add_argument(
        "--favicon", type=Path, required=True, help="Transparent favicon SVG"
    )
    parser.add_argument(
        "--out", type=Path, required=True, help="Output directory, e.g. static/icons"
    )
    parser.add_argument(
        "--browser", help="Path to Chrome or Edge (default: auto-detect)"
    )
    args = parser.parse_args()

    for svg in (args.icon, args.favicon):
        if not svg.is_file():
            logger.error("Not found: %s", svg)
            return 1

    try:
        browser = find_browser(args.browser)
        args.out.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            for name, size in ICON_SIZES.items():
                render(browser, args.icon, size, args.out / name, workdir)
            for name, size in FAVICON_SIZES.items():
                render(browser, args.favicon, size, args.out / name, workdir)
        if args.favicon.resolve() != (args.out / "favicon.svg").resolve():
            shutil.copyfile(args.favicon, args.out / "favicon.svg")
            logger.info("Copied %s", args.out / "favicon.svg")
    except (RenderError, subprocess.TimeoutExpired, OSError):
        logger.exception("Icon rendering failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
