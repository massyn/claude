---
name: devops
description: Git and GitHub workflow — working branches (named after the next PyPI version for packages), staging, commits, pushes, version bumps and pull requests, with hard limits on main/master and on PR approval. Use before running ANY git command that changes state (add, commit, push, merge, rebase, reset, tag, stash, checkout of files), before creating or updating a pull request, and whenever the user asks to commit, save, push, branch, release, publish, bump a version or "ship" work.
---

# Git workflow

## Absolute rules — no exceptions

These hold even if a task seems to require otherwise, and even if asked in passing. If a rule blocks the
task, stop and tell the user; never look for a workaround (such as doing the same thing through
`gh api`, the GitHub web API, or a script).

1. **NEVER run git in the main or master branch. EVER.** Not allowed. Before every git command, run
   `git branch --show-current`. If it prints `main` or `master` (or the repo's default branch), the
   **only** thing you may do on it is bring it up to date, then leave:
   - `git pull --ff-only` — the one and only operation allowed on main. If it cannot fast-forward
     (local main has diverged or has conflicts), stop and tell the user; never merge, rebase or reset
     main to fix it;
   - `git switch -c <branch>` (or `git switch <branch>`) to get off main. Uncommitted changes come along
     to the new branch, so that is the way out when work was started on main.

   Everything else is forbidden while on main/master — `add`, `commit`, `merge`, `rebase`, `reset`,
   `revert`, `cherry-pick`, `stash`, `tag`, `restore`/`checkout` of files, `push`, and any other git
   command.
2. **Never write to main or master from any branch.** No `git push origin main`, no
   `git push origin <branch>:main`, no `HEAD:main`, no merging into main locally. Code reaches main only
   through a pull request that the user merges.
3. **NEVER approve a pull request. That is always the user's job.** No `gh pr review --approve`, no
   approving in the browser or through the API. Equally, never merge a PR (`gh pr merge`), enable
   auto-merge, or dismiss a review.
4. **No history rewriting on pushed branches** — no `push --force`/`--force-with-lease`, no rebasing or
   amending commits that are already pushed — unless the user explicitly asks for that specific action.
5. **No skipping safeguards** — never `--no-verify`, never disable hooks or CI checks to get a commit or
   push through.

## Working branch

All work happens on a working branch, created from an up-to-date main. Every time you start new work:

```bash
git switch main          # commit or finish anything on the current working branch first
git pull --ff-only       # make sure main is the latest — the only command ever run on main
git switch -c <branch>   # leave main immediately
```

If a working branch for this piece of work already exists and its PR is not merged yet, switch to it and
keep going — one branch, one PR.

### Naming

- **Packages published to PyPI:** the branch is named after the version it will release — bare semver,
  no `v` prefix (`1.9.3`, `2.1.0`).
- **Everything else** (Flask apps, config repos): short kebab-case naming the change (`docs`,
  `uptimerobot`, `pwa-tab-bar`).

### Choosing the version (PyPI packages)

1. Find the published version: `https://pypi.org/pypi/<package>/json` → `info.version` (or the version on
   `origin/main` if the package is not published yet).
2. Bump it by semver: **patch** for fixes and data-only changes, **minor** for new features or additive
   columns/options, **major** for anything breaking. If it is unclear which applies, ask.
3. Set the new version in every place the repo keeps it, in the same branch — typically
   `pyproject.toml`, `__version__` in the package's `__init__.py`, and any test asserting the version.
   Find them all with a search for the old version string. CI (e.g. posture's `publish.yml`) fails the PR
   when the locations disagree or the version is not above PyPI's.

## Committing

- Check `git branch --show-current` (rule 1) and `git status` first.
- Stage files by path (`git add path/to/file ...`). Never `git add -A` or `git add .` without reviewing
  `git status` — and never stage secrets (`.env`, `.env_dev`, keys, tokens), local databases or generated
  files (`gunicorn_config.py`, `venv/`, build output).
- Run the project's checks before committing (Makefile `lint`/`format`/`test`, or `ruff`, `black --check`,
  `pytest`). Don't commit with failing checks.
- Commit at logical points. Message: an imperative summary line of 72 characters or fewer
  ("Add Tenable exploit columns"), then a blank line and a short body explaining why, when it isn't obvious.
  British English.

## Pushing

Only ever push the working branch:

```bash
git push -u origin <branch>   # first push
git push                      # afterwards
```

## Pull requests — only when asked

Create a PR only when the user asks for one. Pushing further commits to a branch that already has an
open PR is fine.

```bash
gh pr create --base main --head <branch> --title "<branch>: <one-line summary>" --body-file <file>
```

Title: for a version branch, `1.9.3: Add exploit_available to Tenable.io vulnerabilities`; otherwise a
plain one-line summary. Body:

```markdown
## Summary
- What changed, as bullets — user-visible behaviour first.
- Version bumped to 1.9.3 (`pyproject.toml`, `__init__.py`, `test_posture.py`).

Note anything breaking, or state that the change is additive only.

## Test plan
- [x] What was tested and how, with real results (e.g. "Full suite: 583 passed, 8 skipped")
- [x] `ruff check` and `black --check` clean
```

Then give the user the PR URL and stop. **The user reviews, approves and merges** (rule 3); for PyPI
packages, merging to main triggers the publish workflow.

## After the user merges

Start the next piece of work the same way: `git switch main`, `git pull --ff-only` to pick up the merge,
then `git switch -c <new branch>` (see Working branch). Don't delete merged branches unless asked.
