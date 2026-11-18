# Bundled copies, sweeps and remediation order

Read this when the vulnerable component is a library, codec, parser or runtime that other software is
likely to carry its own copy of. Everything here is generic: the document you write names the product from
the CVE record, never the reader's own machine, venvs or tools.

## Where copies hide

A patched system package does nothing for a copy that something else ships. Check each row that fits the
affected product, and write only the rows that apply into the document's "Where it hides" section.

| Ecosystem | Where the copy lives | How to find it |
|---|---|---|
| OS package | `/usr/lib`, `/usr/lib64`, Homebrew prefix, `C:\Windows\System32` | Package manager query |
| Python wheels | `site-packages/<pkg>/` and `<pkg>.libs/` or `.dylibs/` (auditwheel and delocate vendor shared libraries there) | Search `site-packages` of every environment |
| Python environments | Each venv, each uv tool, each pipx app, each conda env carries its own packages | Search from the home directory, not just the active environment |
| npm | `node_modules/**/*.node` native addons, prebuilt binaries under `prebuilds/` | Search `node_modules` of every project and the global prefix |
| Java | Fat or shaded JARs with the library's classes relocated inside | List JAR contents; the package name may be renamed |
| Go and Rust | Statically linked into the binary; only the build's module list says what is inside | `go version -m <binary>`; `cargo tree` or the SBOM |
| Electron and desktop apps | The app's `resources/` or `Frameworks/` directory | Search the application directories |
| Containers | Image layers; the base image's packages plus anything copied in | Scan the image; rebuild, do not patch in place |
| Caches | Package manager caches (pip, uv, npm, cargo) hold vulnerable archives that reinstall silently | Clear after fixing |

Name a downstream product (a specific package that bundles the component) only when the CVE record, the
vendor advisory or the downstream project's own advisory says so. Otherwise describe the ecosystem pattern
and label it generic.

## The sweep

"Am I affected?" for a bundled component is a search of the whole machine, not one version command. Put
the sweep in the document, written for this CVE: the file name pattern comes from the component's library
name, the ranges from the CPE data. Every sweep must:

- be read-only: it lists and compares, and changes nothing;
- compare versions properly (`sort -V` or `[version]`), never by matching a hardcoded list of patched
  versions, so a later release is not reported as vulnerable;
- take the affected ranges as `start end_exclusive` pairs, one per branch, from the record;
- report `[VULN]`, `[PATCHED]` or `[UNKNOWN]`. A file whose version cannot be read from its name is
  `[UNKNOWN]` with the path, and the document says how to read it (`strings`, file properties, the owning
  package's metadata);
- end by saying what a clean result looks like.

Bash (Linux and macOS). Replace `NAME_GLOB` and the range list:

```bash
verdict() {
    ge() { [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]; }  # $1 >= $2
    for range in "1.0.3 1.0.10" "1.1.0 1.1.1" "1.2.0 1.2.1"; do   # start, end (exclusive)
        set -- $range
        if ge "$ver" "$1" && ! ge "$ver" "$2"; then echo VULN; return; fi
    done
    echo PATCHED
}

find / \( -name "NAME_GLOB*.so*" -o -name "NAME_GLOB*.dylib" \) -not -path "*/.Trash/*" 2>/dev/null |
while read -r f; do
    ver=$(echo "$f" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | tail -1)
    if [ -z "$ver" ]; then echo "[UNKNOWN] $f"; continue; fi
    echo "[$(verdict)] $f ($ver)"
done
```

PowerShell (Windows). The comparison uses `[version]`:

```powershell
$ranges = @(@('1.0.3','1.0.10'), @('1.1.0','1.1.1'), @('1.2.0','1.2.1'))   # start, end (exclusive)
Get-ChildItem -Path $HOME, 'C:\Program Files', 'C:\ProgramData' -Recurse -Filter 'NAME_GLOB*.dll' -ErrorAction SilentlyContinue |
ForEach-Object {
    $v = $_.VersionInfo.ProductVersion
    if (-not $v) { "[UNKNOWN] $($_.FullName)"; return }
    $ver = [version]$v
    $bad = $ranges | Where-Object { $ver -ge [version]$_[0] -and $ver -lt [version]$_[1] }
    "[{0}] {1} ({2})" -f $(if ($bad) { 'VULN' } else { 'PATCHED' }), $_.FullName, $v
}
```

Adapt the file patterns to how the component is really packaged (static `.a` files, `.jar`, `.node`).
Version strings that are not plain `x.y.z` need the pattern changed; say so in the document rather than
leaving a sweep that silently misreports.

## Remediation order

Work down this ladder and stop at the first rung that is possible. Say in the document why a rung is
skipped.

1. **Remove it** if nothing needs it. The smallest attack surface is software that is not installed.
2. **Check what depends on it** before removing or upgrading (`pip show <pkg>` and its `Required-by`,
   `npm ls <pkg>`, `brew uses --installed <pkg>`, the package manager's reverse-dependency query).
3. **Upgrade the owner** of each copy: the system package, the wheel, the npm package, the container base
   image, the application. Upgrading the library alone does not fix a vendored copy.
4. **Confirm the upgrade really contains the fix.** A vendor may release a new version that still bundles
   the old component. Rerun the sweep after every upgrade and trust the sweep, not the version number.
5. **Last resort, if no patched release exists:** isolate it (stop exposing the service, block the vector
   from the CVSS vector string), or delete the bundled copy. Deleting files inside another package's
   directory breaks that package; give it only after the earlier rungs, labelled destructive, and say what
   will stop working.

Mark every command that removes, uninstalls or deletes as destructive in the document, and put the
dependency check before it.

## Environment gotchas

Include only those that apply to the platforms in the document.

- **Externally managed Python** (PEP 668): system and Homebrew Python refuse `pip install`. Use a venv or
  `pipx`, never `--break-system-packages` on a system interpreter.
- **Broken environments**: a venv whose interpreter has been removed cannot run `pip`. Recreate the venv
  from its requirements file instead of editing it.
- **Isolated tool environments** (uv tools, pipx apps): upgrade or reinstall through the tool manager, not
  with the system `pip`.
- **Caches**: clear package caches after the fix so a cached vulnerable archive is not reinstalled.
- **Running processes**: a process keeps the old library mapped until it restarts. Say which services or
  applications to restart.
