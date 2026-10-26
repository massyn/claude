# Housekeeping

A health check of the **current repo only**: bring it up to date, then report on CI, open pull
requests, security alerts and issues. The check itself is read-only. Nothing is written to GitHub and
nothing is changed locally beyond the sync, until the user says yes to a specific fix.

Run the steps in order, then give one report (see Report).

## 1. Sync

Follow "Sync before any work" in the skill. Then look for local branches that are finished:

```bash
git branch --format='%(refname:short)'
gh pr list --head <branch> --state merged --json number,title   # for each branch except main/master
```

List the branches whose PR is confirmed merged and offer to delete them ("After the user merges").
Never delete one on assumption, and leave branches with open, closed-unmerged or no PRs alone.

## 2. CI on main

```bash
gh run list --branch main --limit 5 --json workflowName,status,conclusion,createdAt,url
```

Report the latest run of each workflow. A failed run on main goes at the top of the report.

## 3. Open pull requests: report only

```bash
gh pr list --state open --json number,title,author,headRefName,createdAt,isDraft,reviewDecision,mergeable,statusCheckRollup,closingIssuesReferences
```

For each PR: age, draft or not, CI result, review state, merge conflicts. Group Dependabot PRs
separately. Never approve, merge or comment (rule 3). The most it does is point out a PR that is green
and waiting for the user.

## 4. Security alerts: triage, then offer a fix

```bash
gh api "repos/{owner}/{repo}/dependabot/alerts?state=open" --paginate
gh api "repos/{owner}/{repo}/code-scanning/alerts?state=open" --paginate
gh api "repos/{owner}/{repo}/secret-scanning/alerts?state=open" --paginate
```

- A 403 ("disabled") or 404 ("no analysis found") means the feature is off or not set up. Report it as
  "not enabled", not as a failure. Ignore gh's hint about extra token scopes; the `message` field is
  the real reason.
- Order by severity: secret alerts first, then critical, high, medium, low.
- For each actionable alert, state the fix and end with **"Shall I fix it?"**:
  - **Dependabot:** the version bump that clears it. If a Dependabot PR already does that, point to
    the PR instead.
  - **Code scanning:** the code change, with file and line.
  - **Secret scanning:** rotating the secret is the user's job, so say so. The offer only covers
    removing it from the code.
- Never dismiss, close or reopen an alert. That is the user's call.

## 5. Issues: triage, then offer a fix

```bash
gh issue list --state open --limit 100 --json number,title,author,labels,createdAt,updatedAt,comments
```

Read each issue (`gh issue view <n>` when the title is not enough) and triage it:

- **Type:** bug, feature or question.
- **Priority:** high, medium or low, with a one-line reason.
- **Linked PR:** an open PR whose `closingIssuesReferences` includes it.
- **Stale:** no update in 90 days.

End each issue that could be fixed in this repo with **"Shall I fix it?"**. Write nothing to GitHub:
no comments, labels, assignees or closing. Those are visible to others and need explicit
authorisation for that specific action.

## Report

One report in chat, most urgent first:

1. Red CI on main
2. Secret alerts
3. Critical and high security alerts
4. Other security alerts
5. Open PRs, oldest first
6. Issues, by priority
7. Merged branches that can be deleted

Say "none" for an empty section, and "not enabled" for a security feature that is off. Then stop and
wait.

## When the user says yes

Each approved fix goes through the normal workflow: a working branch from an up-to-date main, checks
run, commit, push. A PR is created only when the user asks for one. A yes covers that fix only, not the
others in the report.

Security scanning of the code itself (Semgrep SAST) is not part of housekeeping. It belongs to the
`sast` skill.
