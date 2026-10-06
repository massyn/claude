---
name: sast
description: Run a Semgrep SAST scan on the current repository, triage findings by severity and exploitability, and produce a remediation plan with a defined auto-fix boundary. Use whenever the user asks to scan a repo for vulnerabilities, run a security/SAST check, review code for security issues, or triage/remediate Semgrep findings — even if they don't say "SAST" or "Semgrep" explicitly.
---

# Semgrep SAST Scan, Triage & Remediation

## 1. Scan

Check semgrep is available first:

```bash
semgrep --version || echo "NOT_INSTALLED"
```

If not installed, tell the user and stop — do not attempt to install tooling silently. Point them to `pip install semgrep --break-system-packages` or their platform's install docs.

**Determine the output location.** This follows the Serif tool's own convention (see `serif_viewer/scan_runner.py` and `scanner.py` in `~/github/projects/active/semgrep`):

```
<serif_dir>/<host>/<owner>/<repo>/<branch>/<timestamp>.sarif
```

- `<serif_dir>` is the `SERIF_DIR` env var if set, otherwise `~/github/projects/active/semgrep/serif`.
- `<host>/<owner>/<repo>` come from the current repo's `origin` remote (SSH or HTTPS), not invented. Fall back to `local/no-owner/<folder-name>` if there's no origin remote.
- `<branch>` is the current branch (`git rev-parse --abbrev-ref HEAD`), or `unknown` if that fails.
- `<timestamp>` uses the format `YYYY-MM-DD-HH-MM-SS`.

```bash
SERIF_DIR="${SERIF_DIR:-$HOME/github/projects/active/semgrep/serif}"
ORIGIN_URL="$(git config --get remote.origin.url)"
# parse ORIGIN_URL into host/owner/repo (git@host:owner/repo.git or https://host/owner/repo)
# fall back to host=local owner=no-owner repo=<folder name> if no origin remote
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
OUTDIR="$SERIF_DIR/<host>/<owner>/<repo>/$BRANCH"
mkdir -p "$OUTDIR"
OUTFILE="$OUTDIR/$(date +%Y-%m-%d-%H-%M-%S).sarif"
```

Run the scan with SARIF output to that location (not just terminal text — SARIF is the source of truth for triage and the reusable artifact for downstream tooling). Use the same ruleset and flags as this project's own Serif scanner (`serif_viewer/scan_runner.py` and `config/scan.yaml` in `~/github/projects/active/semgrep`) rather than `--config=auto` — `auto` alone finds materially fewer issues than the curated configs below:

```bash
semgrep scan --metrics off \
  --config p/default \
  --config p/security-audit \
  --config p/secrets \
  --config p/owasp-top-ten \
  --config p/cwe-top-25 \
  --config p/command-injection \
  --config p/sql-injection \
  --config p/xss \
  --config p/insecure-transport \
  --config p/jwt \
  --config p/secure-defaults \
  --config p/supply-chain \
  --config p/dockerfile \
  --config p/kubernetes \
  --config p/terraform \
  --config p/trailofbits \
  --exclude .github/ --exclude node_modules --exclude vendor --exclude dist --exclude build --exclude .venv \
  --timeout 30 --timeout-threshold 3 --max-target-bytes 2000000 \
  --sarif --output="$OUTFILE" .
```

Scope rules:
- Default to scanning the whole repo, excluding `.github/`, `node_modules`, `vendor`, `dist`, `build`, `.venv`, and anything covered by `.gitignore`.
- If the user asks for "just this PR" or "just what I changed", use `git diff --name-only <base>...HEAD` to scope `--include` flags instead of scanning everything.
- Never silently narrow scope beyond this without telling the user what was excluded and why.
- If `config/scan.yaml` in the Serif project changes its `semgrep:` settings, update this list to match — it is intentionally kept in sync with that file rather than read dynamically.

Parse the SARIF output at `$OUTFILE` (don't re-derive from raw stdout) to get: rule ID, severity, file, line, message, and CWE/OWASP tags if present.

## 2. Triage

Triage every finding against this rubric — don't invent your own scale:

| Priority | Criteria |
|---|---|
| **Critical** | Remote code execution, SQL/command injection, auth bypass, hardcoded production credentials or keys, SSRF reaching internal services |
| **High** | XSS, insecure deserialization, path traversal, broken access control, weak/missing crypto on sensitive data |
| **Medium** | Missing input validation without a clear exploit path, verbose error handling leaking internals, insecure defaults (e.g. debug mode) |
| **Low** | Best-practice deviations, missing security headers, outdated dependency patterns Semgrep flags heuristically |
| **False positive / Not applicable** | Finding is in test/fixture code, behind an auth wall already enforced elsewhere, or Semgrep pattern doesn't match actual data flow |

For each finding, record a one-line justification for its priority — not just the label. If you can't justify why something is Critical vs High from the actual code context, mark it for human review rather than guessing.

**Do not dismiss a finding as a false positive without showing your reasoning.** State what you checked (e.g. "input is sanitized at line 42 via `escape()`") — never dismiss on assumption.

Present triage results as a markdown table:

```markdown
| # | Priority | Rule | File:Line | Issue | Status |
|---|----------|------|-----------|-------|--------|
| 1 | Critical | sql-injection | app/db.py:88 | Unparameterized query built from request input | Needs fix |
| 2 | Low | missing-header | app/server.py:12 | No `X-Frame-Options` header set | Needs fix |
| 3 | — | hardcoded-secret | tests/fixtures.py:5 | Test fixture, not real credential | False positive |
```

## 3. Remediation

**Auto-fix boundary — do not cross this without explicit user approval:**

Safe to fix directly:
- Missing input sanitization/escaping with an obvious, narrow fix (e.g. parameterize a query, escape output)
- Missing security headers
- Insecure default config flags (e.g. `debug=True` in production config)
- Outdated/insecure function calls with a clear drop-in replacement (e.g. `md5` → `sha256` for non-password hashing)
- `github-actions-mutable-action-tag` findings — pin the action to the immutable commit SHA it currently resolves to (keep the version as a trailing comment, e.g. `uses: actions/checkout@<sha> # v4`)

Requires explicit approval before touching:
- Anything in authentication, authorization, or session handling
- Anything in cryptography or key management
- Anything in deserialization of untrusted data
- Any fix that changes a public API contract or database schema

Never do:
- Suppress a finding with a `# nosemgrep` / inline ignore comment on your own judgement — see the Suppression rule below
- Fix a finding you couldn't confidently triage in step 2

**Suppression (false positives).** Do not suppress anything by default — a finding marked "False positive" in triage stays visible on every future scan until the user explicitly confirms it. Only after the user has reviewed a specific finding and explicitly confirmed it's a false positive (not just accepted the triage table as a whole) may you suppress it, using `# nosemgrep: <rule-id>` on the exact flagged line.

Every suppression comment must carry a dated, attributable reason — never a bare `# nosemgrep`. Use this fixed format so entries stay greppable and auditable:

```python
query = build_query(user_id)  # nosemgrep: sql-injection -- 2026-09-12, confirmed by <user>: user_id validated as int at api/routes.py:12
```

Fields, in order, separated by `, `:
- `<rule-id>` — the exact Semgrep rule ID, after `nosemgrep:`
- date — the date of the user's confirmation, `YYYY-MM-DD`, not the scan date
- `confirmed by <user>` — who approved the suppression (ask if not obvious from context; never write a name you're inferring)
- the reason itself — reference the actual code/control that makes it safe, not a restatement of the rule

Rules for suppression:
- One finding per suppression — never suppress a whole rule repo-wide or add a blanket `.semgrepignore` entry without the user separately asking for that broader scope.
- If the user's confirmation is ambiguous about which specific findings they mean, ask before suppressing rather than guessing.
- Note each suppression applied against its row in the triage table (Status → "Suppressed") in the summary, and include the same date/confirmer/reason there so the table and the code stay consistent.
- Never edit or remove an existing `nosemgrep` suppression comment left by someone else without the user's explicit instruction — treat it as an audit record, not dead code.

For each fix applied, note it against its row in the triage table (Status → "Fixed") and show a brief diff summary. For anything requiring approval, list it separately and wait for a yes before touching the code.

## 4. Summary output

Close with:
- Total findings by priority (table)
- What was auto-fixed vs what's pending approval vs what's false positive
- The SARIF file path (`$OUTFILE`) under `<serif_dir>/<host>/<owner>/<repo>/<branch>/`, since it's the reusable artifact the Serif viewer picks up for other tooling