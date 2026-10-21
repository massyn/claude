# Deployment and environment

Flask apps are deployed with [flask-deploy](https://github.com/massyn/flask-deploy) — a curl-able bash
script that installs the app behind Gunicorn + Nginx + systemd on an Ubuntu/Debian server. The script
itself stays in the flask-deploy repo (CI workflows curl it from `raw.githubusercontent.com`); this file
documents the contract an app must meet. The GitHub Actions runner packages the app and copies it to the
server; the server never pulls from GitHub, so private repos need no token there.

## App contract

| Requirement | Detail |
|-------------|--------|
| `run.py` at repo root | Exposes module-level `app`; Gunicorn runs `run:app` — filename and variable name are fixed |
| `requirements.txt` at repo root | Must list `gunicorn` |
| `.gitignore` | Must exclude `venv/`, `gunicorn_config.py`, `.env`, `.env_dev` |
| `DATABASE_URL` | For SQLite in production must point to `/data/<slug>/app.db` so it survives redeploys |

`gunicorn_config.py` and `venv/` are generated on the server on every deploy — never commit them.

### `run.py`

```python
import os
from pathlib import Path
from dotenv import load_dotenv

_env_file = Path('.env_dev') if Path('.env_dev').exists() else Path('.env')
load_dotenv(_env_file)

from app import create_app  # noqa: E402 — must load env before importing config

app = create_app()

if __name__ == '__main__':
    app.run(
        host=os.environ.get('FLASK_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
    )
```

`load_dotenv()` must run before anything imports `config`. `FLASK_HOST`, `FLASK_PORT` and
`FLASK_DEBUG` are only read in the `__main__` block — Gunicorn controls binding in production.

## Environment files

| File | Committed | Purpose |
|------|-----------|---------|
| `.env.example` | Yes | Documents every variable the app reads |
| `.env_dev` | No | Local developer overrides; loaded in preference to `.env` when present |
| `.env` | No | Production values; built by GitHub Actions at deploy time and delivered to the server |

Local dev: copy `.env.example` to `.env_dev` and fill in values (Bitwarden is the source of truth for
secret values). Set `FLASK_DEBUG=True`. Do not set `FORCE_HTTPS` locally.

### Variables

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Flask session signing — must be replaced in production |
| `DATABASE_URL` | Required, no default. `sqlite:////data/<slug>/app.db` or a Postgres URL |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google OAuth credentials |
| `APP_HOSTNAME` | Comma-separated allow-list of valid hostnames (see `security.md`) |
| `FORCE_HTTPS` | `true` for non-Cloudflare HTTPS deployments; omit behind Cloudflare and in local dev |
| `VERSION` | Footer version label; generated at deploy time, not stored as a secret |
| `GTAG_ID` | Google tag ID; omit to render no analytics tag |
| `FLASK_PORT` | Dev only — dev server port (default 5000). Omit in production; flask-deploy assigns the port |
| `FLASK_DEBUG` | Dev only — enables debug and disables `SESSION_COOKIE_SECURE` |
| `TEST_USER` | Dev only — bypasses Google OAuth (see `security.md`) |

## Server directory layout

| Path | Purpose |
|------|---------|
| `/opt/<slug>/` | App code unpacked from the deploy archive — disposable; `venv/` and `.env` are kept across deploys |
| `/data/<slug>/` | Stateful data: SQLite databases, TLS certs — **backed up to S3** |
| `/var/log/<slug>/` | `access.log`, `error.log` (Gunicorn), `nginx.access.log`, `nginx.error.log` |

## deploy.sh flags

| Flag | Description |
|------|-------------|
| `--slug` | Required. App identifier — used for directory and service names |
| `--domain` | Required. Nginx `server_name` value(s), space-separated |
| `--source` | Path to a `.tar.gz` of the app on the server (from `git archive` on the runner); deleted once unpacked. Use this, not `--repo` |
| `--repo` | Legacy alternative to `--source`: the server clones the Git URL itself. Do not use for new apps |
| `--env` | Path to a `.env` file; moved (not copied) into the app directory |
| `--ssl` | HTTPS using `/data/<slug>/public.pem` and `/data/<slug>/private.pem` |
| `--cloudflare` | Only allow traffic from Cloudflare IP ranges |
| `--password` | HTTP basic auth (username `admin`) |
| `--dry-run` | Validate the repository only; no server changes |

Dry-run output — `[✗]` fails the run, `[!]` is a warning:

```
[✓] run.py found
[✓] requirements.txt found
[✓] gunicorn in requirements.txt
[✓] app object found in run.py
[!] .env missing
[!] DATABASE_URL not pointing to /data/<slug>/
```

## GitHub Actions workflow

Secrets live in GitHub Actions secrets. The runner checks out the commit, packages it with `git archive`,
builds the `.env` fresh and `scp`s both to the server — the `.env` is never committed. Only `SLUG` and
`HOSTS` change per app.

```yaml
name: Deploy

on:
  push:
    branches: ['main']

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      SLUG: myapp
      HOSTS: "myapp.com www.myapp.com"

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure SSH
        run: |
          mkdir -p ~/.ssh/
          echo "${{ secrets.SSH_KEY }}" > ~/.ssh/external-machine.key
          chmod 600 ~/.ssh/external-machine.key
          cat >>~/.ssh/config <<END
          Host external-machine
            HostName ${{ secrets.SSH_HOST }}
            User ${{ secrets.SSH_USER }}
            Port 22
            IdentityFile ~/.ssh/external-machine.key
            StrictHostKeyChecking no
          END

      - name: Create .env file
        run: |
          echo "# created from actions" > .env
          echo "SECRET_KEY=${{ secrets.SECRET_KEY }}" >> .env
          echo "DATABASE_URL=sqlite:////data/${{ env.SLUG }}/app.db" >> .env
          echo "GOOGLE_CLIENT_ID=${{ secrets.GOOGLE_CLIENT_ID }}" >> .env
          echo "GOOGLE_CLIENT_SECRET=${{ secrets.GOOGLE_CLIENT_SECRET }}" >> .env
          echo "APP_HOSTNAME=$(echo '${{ env.HOSTS }}' | tr ' ' ',')" >> .env
          echo "VERSION=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> .env

      - name: Package app
        run: git archive --format=tar.gz -o app.tar.gz HEAD

      - name: Copy app and .env to server
        run: |
          scp app.tar.gz external-machine:/tmp/${{ env.SLUG }}.tar.gz
          scp .env external-machine:/tmp/${{ env.SLUG }}.env

      - name: Deploy Flask
        run: ssh external-machine "curl -fsSL https://raw.githubusercontent.com/massyn/flask-deploy/main/deploy.sh | sudo bash -s -- --slug ${{ env.SLUG }} --domain \"${{ env.HOSTS }}\" --source /tmp/${{ env.SLUG }}.tar.gz --ssl --cloudflare --env /tmp/${{ env.SLUG }}.env"

  notify:
    needs: [deploy]
    if: ${{ !cancelled() && github.ref == 'refs/heads/main' && !contains(needs.*.result, 'cancelled') }}
    runs-on: ubuntu-latest
    steps:
      - name: Notify Slack
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
          RESULT: ${{ contains(needs.*.result, 'failure') && 'failure' || 'success' }}
          REPO: ${{ github.repository }}
          WORKFLOW: ${{ github.workflow }}
          BRANCH: ${{ github.ref_name }}
          SHA: ${{ github.sha }}
          ACTOR: ${{ github.actor }}
          COMMIT_MSG: ${{ github.event.head_commit.message }}
          SERVER: ${{ github.server_url }}
          RUN_ID: ${{ github.run_id }}
        run: |
          if [ -z "$SLACK_WEBHOOK" ]; then
            echo "::warning::SLACK_WEBHOOK secret is not set; skipping Slack notification"
            exit 0
          fi
          if [ "$RESULT" = success ]; then
            colour="#2eb886"; title="Build succeeded"
          else
            colour="#a30200"; title="Build failed"
          fi
          payload=$(jq -n \
            --arg colour "$colour" \
            --arg title "$title: $REPO" \
            --arg run_url "$SERVER/$REPO/actions/runs/$RUN_ID" \
            --arg commit "<$SERVER/$REPO/commit/$SHA|${SHA:0:7}>" \
            --arg message "${COMMIT_MSG%%$'\n'*}" \
            --arg workflow "$WORKFLOW" \
            --arg branch "$BRANCH" \
            --arg actor "$ACTOR" \
            '{attachments: [{
              color: $colour,
              fallback: $title,
              title: $title,
              title_link: $run_url,
              text: $message,
              fields: [
                {title: "Workflow", value: $workflow, short: true},
                {title: "Branch", value: $branch, short: true},
                {title: "Commit", value: $commit, short: true},
                {title: "Triggered by", value: $actor, short: true}
              ],
              ts: (now | floor)
            }]}')
          curl -fsS -X POST -H 'Content-Type: application/json' -d "$payload" "$SLACK_WEBHOOK" \
            || echo "::warning::Slack notification failed"
```

- `git archive` packages committed files only, so `.git`, `venv/` and `.env` never ship. Each deploy
  replaces everything in `/opt/<slug>/` except `venv/` and `.env`.
- The first `.env` line uses `>` so each run starts clean; every other line appends with `>>`.
- `APP_HOSTNAME` is derived from `HOSTS` — `tr` turns the space-separated list into the comma-separated
  allow-list `config.py` expects. Writing `APP_HOSTNAME=${{ env.HOSTS }}` directly breaks multi-host apps.
- `DATABASE_URL` for SQLite is derived from `SLUG`, not stored as a secret.
- Drop `--ssl` if the app has no origin certificate.
- Every new secret needs its own line here — intentional, keeps the wiring explicit.
- Load secrets into GitHub with `gh secret set --env-file .env` (commented lines are ignored).
- The `notify` job is the standard Slack build notification from the devops skill
  (`devops/references/ci-notify.md`), which also covers creating the `SLACK_WEBHOOK` secret from
  `~/github/.env`. Keep the two in step when changing the template.

## Standing up a new site

1. Register the domain; delegate DNS to Cloudflare and delete any Route 53 hosted zone.
2. In Cloudflare, proxy CNAMEs for `@` and `www` to the droplet FQDN.
3. Create a Cloudflare Origin Certificate (domain + wildcard) and install it on the server as
   `/data/<slug>/public.pem` and `/data/<slug>/private.pem` (`chmod 600` the key). Set Cloudflare SSL
   mode to **Full (strict)**.
4. If the app uses Google login, create an OAuth client with redirect URI
   `https://<domain>/auth/callback`.
5. Load the app's secrets and `SLACK_WEBHOOK` into GitHub Actions secrets and add the workflow above.
6. Push to `main` and watch the Actions log.
