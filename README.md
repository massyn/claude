# claude
Configuration for Claude Code: global instructions, settings, and a plugin marketplace of skills and commands.

| Path | Purpose |
|------|---------|
| [CLAUDE.md](CLAUDE.md) | Universal behaviour rules — copied to `~/.claude/CLAUDE.md` |
| [settings.json](settings.json) | Permissions and plugin registration — merged into `~/.claude/settings.json` |
| [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json) | Makes this repo the `massyn-tools` plugin marketplace |
| [plugins/massyn/](plugins/massyn/) | The `massyn` plugin — skills and commands |
| [deploy.py](deploy.py) | Syncs `CLAUDE.md` and `settings.json` into `~/.claude` |

## The `massyn` plugin

| Component | Invoke as | Purpose |
|-----------|-----------|---------|
| `skills/devops` | `massyn:devops` | Git workflow: working branches (PyPI version names), commits, PRs — never on main, never approves PRs |
| `skills/python` | `massyn:python` | Python conventions (typing, dotenv, logging, black/ruff, pytest) |
| `skills/flask` | `massyn:flask` | Flask app conventions, golden template, flask-deploy contract |
| `skills/flask-pwa` | `massyn:flask-pwa` | Installable phone-first Flask apps: manifest, icons, service worker, bottom tab bar |
| `skills/sast` | `massyn:sast` | Semgrep SAST scan, triage and remediation plan |
| `commands/coffee.md` | `/massyn:coffee` | Write a session handoff (local + Citadel) before `/clear` |

Skills load automatically when a task matches their description.

## Install on a machine

```bash
python deploy.py
```

This copies `CLAUDE.md`, adds any missing permissions, and registers the marketplace (`extraKnownMarketplaces`)
with the plugin enabled (`enabledPlugins`). Start a new Claude Code session and it fetches the plugin from
GitHub. Check with `claude plugin list`.

Without `deploy.py`, the same result by hand:

```bash
claude plugin marketplace add massyn/claude
claude plugin install massyn@massyn-tools
```

## Updating

Push to `main`. The marketplace has `autoUpdate` on, so each machine picks up the new commit during its next
session (then `/reload-plugins`, or restart). To update immediately: `claude plugin update massyn@massyn-tools`.

The plugin deliberately has no `version` field — Claude Code uses the commit SHA as the version, so every push
is an update. `claude plugin validate` warns about the missing version; that warning is expected.

## Developing locally

To test edits without pushing, point a session at the working copy:

```bash
claude --plugin-dir ./plugins/massyn
```

Validate after changing a manifest or adding a component:

```bash
claude plugin validate .
```
