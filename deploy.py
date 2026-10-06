"""
deploy.py — sync the repo settings.json into ~/.claude/settings.json and copy CLAUDE.md.

Synced settings:
  - permissions/allow and permissions/deny
  - extraKnownMarketplaces and enabledPlugins (registers the massyn-tools plugin marketplace;
    Claude Code fetches and installs the enabled plugins at the next session start)

Rules:
  - Entries in source but missing from target → added to target.
  - Entries in target but missing from source → reported as proposals (not modified).
  - Keys present in both with different values → reported as conflicts (not modified).
  - Nothing is ever removed from target.
"""

import difflib
import json
import shutil
import sys
from pathlib import Path


SOURCE = Path(__file__).parent / "settings.json"
TARGET = Path.home() / ".claude" / "settings.json"

PLUGIN_SECTIONS = ("extraKnownMarketplaces", "enabledPlugins")

DOCS_TO_COPY: list[tuple[Path, Path]] = [
    (Path(__file__).parent / "CLAUDE.md", Path.home() / ".claude" / "CLAUDE.md"),
]


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


def sync_mapping(section: str, source_map: dict, target_map: dict) -> bool:
    """Add keys missing from target_map; report the rest. Returns True if target_map changed."""
    to_add = sorted(set(source_map) - set(target_map))
    proposals = sorted(set(target_map) - set(source_map))
    conflicts = sorted(
        k for k in set(source_map) & set(target_map) if source_map[k] != target_map[k]
    )

    if to_add:
        print(f"\n{section} — adding {len(to_add)} new key(s):")
        for key in to_add:
            print(f"  + {key}")
            target_map[key] = source_map[key]
    else:
        print(f"\n{section} — nothing to add.")

    if conflicts:
        print(f"\n{section} — {len(conflicts)} key(s) differ between source and target (target kept):")
        for key in conflicts:
            print(f"  ! {key}: source={json.dumps(source_map[key])} target={json.dumps(target_map[key])}")

    if proposals:
        print(f"\n{section} — {len(proposals)} key(s) in target but NOT in source (proposals to add to repo):")
        for key in proposals:
            print(f"  ? {key}")

    return bool(to_add)


def sync_file(source: Path, target: Path) -> None:
    name = source.name
    if not source.exists():
        print(f"{name} — source not found, skipping: {source}", file=sys.stderr)
        return

    source_lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
    target_lines = (
        target.read_text(encoding="utf-8").splitlines(keepends=True)
        if target.exists()
        else []
    )

    diff = list(difflib.unified_diff(
        target_lines,
        source_lines,
        fromfile=str(target),
        tofile=str(source),
    ))

    if not diff:
        print(f"\n{name} — no changes.")
        return

    print(f"\n{name} — diff:")
    print("".join(diff), end="")
    shutil.copy2(source, target)
    print(f"\n{name} — copied to {target}")


def main() -> int:
    # Diffs of CLAUDE.md contain non-ASCII characters; Windows defaults to cp1252 when piped.
    sys.stdout.reconfigure(encoding="utf-8")

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

    for section in PLUGIN_SECTIONS:
        if sync_mapping(section, source.get(section, {}), target.setdefault(section, {})):
            changed = True
        elif not target[section]:
            del target[section]

    if changed:
        save(TARGET, target)
        print(f"\nTarget updated: {TARGET}")
    else:
        print(f"\nTarget unchanged: {TARGET}")

    for src, tgt in DOCS_TO_COPY:
        sync_file(src, tgt)

    return 0


if __name__ == "__main__":
    sys.exit(main())
