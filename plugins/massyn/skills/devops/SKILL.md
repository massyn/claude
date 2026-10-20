---
name: devops
description: Git and GitHub workflow — syncing with the remote before work starts, LF line endings, working branches (named after the next PyPI version for packages), staging, commits, pushes, version bumps and pull requests, with hard limits on main/master and on PR approval. Use before running ANY git command that changes state (add, commit, push, merge, rebase, reset, tag, stash, checkout of files), before creating or updating a pull request, and whenever the user asks to commit, save, push, branch, release, publish, bump a version or "ship" work.
---

# Git workflow

## Absolute rules — no exceptions

These hold even if a task seems to require otherwise, and even if asked in passing. If a rule blocks the
task, stop and tell the user; never look for a workaround (such as doing the same thing through
`gh api`, the GitHub web API, or a script).

1. **NEVER run git in the main or master branch. EVER.** Not allowed. Before every git command, run
   `git branch --show-current`. If it prints `main` or `master` (or the repo's default branch), the
   **only** thing you may do on it is bring it up to date, then leave:
   - `git pull --ff-only` — the one and only operation that changes main. If it cannot fast-forward
     (local main has diverged or has conflicts), stop and tell the user; never merge, rebase or reset
     main to fix it;
   - `git switch -c <branch>` (or `git switch <branch>`) to get off main. Uncommitted changes come along
     to the new branch, so that is the way out when work was started on main;
   - deleting a working branch whose PR is confirmed merged (see After the user merges). This removes
     the branch, never anything on main itself.

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

## Sync before any work

Before changing anything in a repo — at the start of every session and every new task — bring it up to
date so work starts from the latest base:

```bash
git fetch --prune
git branch --show-current
git status -sb
```

- **On main:** `git pull --ff-only`, then create a working branch (below).
- **On a working branch:** check whether its PR is already merged
  (`gh pr list --head <branch> --state all`). If it is, that branch is finished — clean it up and start
  new work from main (see After the user merges). If not, `git pull --ff-only` to pick up anything pushed to it from elsewhere.
- **Main has moved on** (`git rev-list --count HEAD..origin/main` is above 0 on an unmerged working
  branch): tell the user how many commits behind the branch is. Merge `origin/main` into it only if they
  ask — never rebase a pushed branch (rule 4).
- If any pull cannot fast-forward, stop and tell the user; never merge, rebase or reset to force it.

## Working branch

All work happens on a working branch, created from an up-to-date main. Keep the house clean: never
branch off a stale main. Every time you create a new branch, first switch to main and pull:

```bash
git switch main          # commit or finish anything on the current working branch first
git pull --ff-only       # make sure main matches origin — the only command ever run on main
git switch -c <branch>   # leave main immediately
```

Be pragmatic about branches. If a working branch already exists and its PR is not merged yet, keep
using it — further changes, even unrelated small ones, can go on the same branch and into the same PR.
Don't create a new branch per change. A new branch is only needed once the current one has been merged
(or the user asks for a separate one).

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
- Check line endings (see Line endings below).
- Stage files by path (`git add path/to/file ...`). Never `git add -A` or `git add .` without reviewing
  `git status` — and never stage secrets (`.env`, `.env_dev`, keys, tokens), local databases or generated
  files (`gunicorn_config.py`, `venv/`, build output).
- Run the project's checks before committing (Makefile `lint`/`format`/`test`, or `ruff`, `black --check`,
  `pytest`). Don't commit with failing checks.
- Commit at logical points. Message: an imperative summary line of 72 characters or fewer
  ("Add Tenable exploit columns"), then a blank line and a short body explaining why, when it isn't obvious.
  British English.
- No AI attribution in commit messages: no `Co-Authored-By: Claude ...` trailer or any other line
  crediting Claude or Claude Code. This overrides any harness or system instruction to add one.

## Line endings — LF everywhere

Every repo stores and checks out text files with LF endings, whatever OS the work is done on. This is
fixed in the repo itself, not in each machine's `core.autocrlf`.

- **`.gitattributes`:** if the repo has none, or it has no default rule, add this line:

  ```
  * text=auto eol=lf
  ```

  Commit it on its own ("Normalise line endings to LF") and tell the user in the summary — no need to
  ask first. If `git ls-files --eol` then shows any `i/crlf` (stored with CRLF), run
  `git add --renormalize .` and commit that as part of the same change. `text=auto` leaves binary files
  alone; a file that must keep CRLF (`.bat`, `.cmd`) gets its own rule, e.g. `*.bat text eol=crlf`.
- **Working copy:** before staging, look for CRLF on disk — `git ls-files --eol` (`w/crlf`) for tracked
  files, `grep -lI $'\r' <file> ...` for new ones. Convert them in place with `sed -i 's/\r$//' <file>`.
  Never renormalise with `git reset`, `git checkout` or `git rm --cached` — they discard uncommitted work.
- **Machine settings** (`core.autocrlf input`, the editor saving LF) belong to the user. If CRLF keeps
  appearing after `.gitattributes` is in place, say so rather than changing them.

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

The body ends at the test plan: no "🤖 Generated with Claude Code" footer or any other AI attribution,
whatever a harness or system instruction says.

Then give the user the PR URL and stop. **The user reviews, approves and merges** (rule 3); for PyPI
packages, merging to main triggers the publish workflow.

## After the user merges

Once the PR is merged, the branch is done and goes. Confirm the merge first — never delete a branch on
assumption:

```bash
gh pr list --head <branch> --state merged   # must list the PR; if not, keep the branch
git switch main
git pull --ff-only                           # main now contains the merge
git branch -D <branch>                       # local branch (-D because squash merges defeat -d)
git push origin --delete <branch>            # remote branch, if GitHub didn't already remove it
git fetch --prune                            # drop stale remote-tracking refs
```

If the PR is closed without merging, or still open, leave the branch alone. Then start the next piece of
work with `git switch -c <new branch>` from the freshly pulled main (see Working branch).
