---
description: Write a handoff note (local + Citadel), then stop so the user can /clear
---

You are about to be reset. This is a coffee break, not a failure. Write a clean handoff so the next session picks up exactly where you left off, with no drift and no re-litigating decisions already made.

## Step 1 - Identify the project

Determine the current project's Citadel room slug (e.g. ccm-api, insight, simple-bank). If unclear, check recent file paths or ask the user in one line.

## Step 2 - Write .claude/HANDOFF.md in the repo root

Overwrite the file entirely (don't append) with this structure:

```markdown
# Handoff - <project> - <ISO datetime>

## Current task
<One or two sentences: what was explicitly asked for, verbatim where possible.>

## Status
<Done / in progress / blocked. Be precise. "Mostly working" is not a status.>

## Files touched this session
- path/to/file.py - <what changed, one line>
- path/to/other.py - <what changed, one line>

## Explicit scope boundaries
<What you were told NOT to touch, change, or add. If nothing was said, write "Not specified - ask before expanding scope.">

## Unrequested changes made this session
<Anything you did that wasn't explicitly asked for: refactors, added functionality, API changes. List it honestly even if unflattering. "None" if none. This file is read by the next instance of you - omitting this just reproduces the problem the user is trying to solve.>

## Next step
<The single next action. One thing, not a list of options.>

## Open questions / decisions needed
<Anything the user needs to weigh in on before work continues. "None" if none.>
```

Rules for filling this in:
- Do not editorialise, do not pad, do not write this in a "summary of accomplishments" tone. This is a shift handover, not a highlight reel.
- Keep it under ~40 lines. If it's longer, the task was too big for one handoff. Say so under Next step.

## Step 3 - Write the same content to Citadel

Call Citadel:add_entry with:
- room: the project's own Citadel room slug (never a separate handoffs room, per autoexec rules)
- title: Handoff - <ISO date>
- summary: the Current task + Status lines, one paragraph
- detail: the full markdown from Step 2
- tags: ["context"] if this entry should become the room's living context entry, otherwise ["spec"]. Max 3 tags, semantic only, per autoexec.

If the room already has a context entry, update it (Citadel:update_entry) rather than creating a duplicate. Check Citadel:get_room first.

## Step 4 - Stop

Output exactly this, then stop coding for this session:

```
Handoff written to .claude/HANDOFF.md and logged to Citadel (<room>).
Ready for /clear when you are. Paste HANDOFF.md back in to resume.
```

Do not start the next task. Do not ask "anything else?". Wait for the user's next message. The point of /coffee is to end this context cleanly, not to keep working inside a context that's about to be cleared.
