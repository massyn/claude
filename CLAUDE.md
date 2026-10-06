## General

- If ambiguity is minor and reversible, proceed with a sensible assumption and state it.
- Use British English spelling for all communication, comments, and code.
- Git: follow the `massyn:devops` skill. NEVER run git in the main or master branch — the only thing allowed on main is `git pull --ff-only` to bring it up to date before branching; no add, commit, merge, push or anything else there, ever. Work only on a working branch. NEVER approve or merge a pull request — that is always the user's job.
- When completing tasks from a dev plan checklist, check off tasks as you complete them.
- Only modify files within the current project directory. If a root cause lies in an external project or dependency, report it and ask before acting.
- Only make changes that were explicitly requested. This applies to code, configuration, files, and documentation alike. If you notice something outside the stated task that appears incorrect or improvable, report it as a finding and wait for instruction. Do not act on it.
- When diagnosing a problem outside your scope, stop at the diagnosis. Present findings and wait for instruction.

## Decision Gates

- When a request contains both an implementation ask AND a design/recommendation ask, treat the recommendation as a decision gate. Do not implement the design portion until the user has reviewed the options and explicitly chosen one.
- "Provide recommendations", "suggest", "advise", "what do you think", "how should we" — any of these phrases in a request means stop and present options. Do not proceed past that point without explicit approval.

## Project Structure

- Group code by functional concern, not by type.
- A file should have one clear reason to exist — if you can't describe its purpose in a sentence, it needs splitting.
- Don't extract helper functions unless they are reused or genuinely simplify a complex body of logic. An inner function or inline expression is preferable to a private module-level function used in only one place.
- Entry points (app.py, main.py, cli.py) are wiring only — no business logic.
- Do not grow a single file to accommodate new concerns. Create a new file instead.
- Configuration must be externalised (env/config files), not hardcoded in business logic.
- Log meaningful events and errors at appropriate levels; avoid print debugging.

## Code Quality

- Implement actual functionality — no mock, placeholder, or stub code.
- Prefer simple, concise solutions. Favour designs that are easy to extend without major refactoring.
- If a file exceeds 400 lines, treat it as a signal to reconsider structure — not a hard limit to write up to.
- Handle errors explicitly. Prefer returning errors or raising specific exceptions over silent failures or bare excepts.
- Variables should have sensible defaults but be parameterised and available as configuration options where appropriate.
- Find root causes. No temporary fixes. Senior developer standards.
- For non-trivial changes, pause and ask "is there a more elegant way?" — skip this for simple, obvious fixes.
- If a solution feels hacky, step back and implement the elegant one instead.

## Skills

- Stack-specific conventions live in skills (from the `massyn` plugin), not in this file. Load the matching skill before writing code:
  - Any git or GitHub operation (branch, commit, push, version bump, pull request) → `massyn:devops`
  - Any Python code → `massyn:python`
  - Flask web apps (including SQL templates, Bootstrap/Jinja2 UI, flask-deploy) → `massyn:flask`, in addition to `massyn:python`
  - Installable / phone-first Flask apps (PWA, bottom tab bar, app icons, service worker) → `massyn:flask-pwa`, in addition to `massyn:flask`

## Tools

- Prioritise using available tools over manual approaches whenever appropriate.
- Use `-q` (quiet) flags where available for package installation and similar commands. Only surface output if the command exits with an error.

## Citadel

- When starting work on a Citadel todo, mark it in_progress immediately.
- When finishing work that was tracked as a Citadel todo, close it. Do not wait to be asked.
- Do not make commitments about future behaviour across sessions. You have no persistent memory and cannot enforce them. Acknowledge the limitation honestly instead.

## Communication

- Be concise in explanations. Do not narrate every step — summarise what you did and flag anything unexpected.
- Do not re-read files you have already read in this session unless the content may have changed.
- When given a bug report, just fix it — diagnose from logs and errors without asking for hand-holding.
- Do not make reassuring statements you cannot back up. If you cannot guarantee something, say so.
