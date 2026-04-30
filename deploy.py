"""
deploy.py — sync permissions from the repo settings.json into ~/.claude/settings.json.

Rules:
  - Entries in source but missing from target → added to target.
  - Entries in target but missing from source → reported as proposals (not modified).
  - Nothing is ever removed from target.
"""

import difflib
import json
import shutil
import sys
from pathlib import Path


SOURCE = Path(__file__).parent / "settings.json"
TARGET = Path.home() / ".claude" / "settings.json"

CLAUDE_MD_SOURCE = Path(__file__).parent / "CLAUDE.md"
CLAUDE_MD_TARGET = Path.home() / ".claude" / "CLAUDE.md"


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def save(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def sync_list(
    section: str,
    source_items: list[str],
    target_items: list[str],
) -> tuple[list[str], list[str], list[str]]:
    """Return (to_add, proposals, unchanged)."""
    source_set = set(source_items)
    target_set = set(target_items)

    to_add = sorted(source_set - target_set)
    proposals = sorted(target_set - source_set)

    return to_add, proposals


def sync_claude_md() -> None:
    if not CLAUDE_MD_SOURCE.exists():
        print(f"CLAUDE.md — source not found, skipping: {CLAUDE_MD_SOURCE}", file=sys.stderr)
        return

    source_lines = CLAUDE_MD_SOURCE.read_text(encoding="utf-8").splitlines(keepends=True)
    target_lines = (
        CLAUDE_MD_TARGET.read_text(encoding="utf-8").splitlines(keepends=True)
        if CLAUDE_MD_TARGET.exists()
        else []
    )

    diff = list(difflib.unified_diff(
        target_lines,
        source_lines,
        fromfile=str(CLAUDE_MD_TARGET),
        tofile=str(CLAUDE_MD_SOURCE),
    ))

    if not diff:
        print("\nCLAUDE.md — no changes.")
        return

    print("\nCLAUDE.md — diff:")
    print("".join(diff), end="")
    shutil.copy2(CLAUDE_MD_SOURCE, CLAUDE_MD_TARGET)
    print(f"\nCLAUDE.md — copied to {CLAUDE_MD_TARGET}")


def main() -> int:
    if not SOURCE.exists():
        print(f"ERROR: source not found: {SOURCE}", file=sys.stderr)
        return 1
    if not TARGET.exists():
        print(f"ERROR: target not found: {TARGET}", file=sys.stderr)
        return 1

    source = load(SOURCE)
    target = load(TARGET)

    source_perms = source.get("permissions", {})
    target_perms = target.setdefault("permissions", {})

    changed = False

    for section in ("allow", "deny"):
        source_items: list[str] = source_perms.get(section, [])
        target_items: list[str] = target_perms.setdefault(section, [])

        to_add, proposals = sync_list(section, source_items, target_items)

        if to_add:
            print(f"\npermissions/{section} — adding {len(to_add)} new entr{'y' if len(to_add) == 1 else 'ies'}:")
            for item in to_add:
                print(f"  + {item}")
                target_items.append(item)
            changed = True
        else:
            print(f"\npermissions/{section} — nothing to add.")

        if proposals:
            print(f"\npermissions/{section} — {len(proposals)} entr{'y' if len(proposals) == 1 else 'ies'} in target but NOT in source (proposals to add to repo):")
            for item in proposals:
                print(f"  ? {item}")

    if changed:
        save(TARGET, target)
        print(f"\nTarget updated: {TARGET}")
    else:
        print(f"\nTarget unchanged: {TARGET}")

    sync_claude_md()

    return 0


if __name__ == "__main__":
    sys.exit(main())
