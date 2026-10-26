---
description: Sync the current repo, then triage CI, open PRs, security alerts and issues (read-only)
---

Load the `massyn:devops` skill, then run the housekeeping job in its `references/housekeeping.md`
on the current repo only.

The check is read-only. Give the report, offer "Shall I fix it?" where a fix applies, then stop and
wait. Do not fix, comment, label, close, approve or merge anything without the user's explicit yes for
that specific item.
