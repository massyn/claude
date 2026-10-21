# Slack build notifications

Every GitHub Actions workflow that builds, tests, deploys or publishes from `main` ends with a `notify`
job that posts the result to Slack: green for success, red for failure. Cancelled runs and runs on any
other ref (pull requests, feature branches) post nothing.

## The secret

The webhook URL lives in `~/github/.env` as `SLACK_WEBHOOK=...` and in each repo as the Actions secret
`SLACK_WEBHOOK`. Before adding or editing a workflow, make sure the repo has it:

```bash
if gh secret list --json name -q '.[].name' | grep -qx SLACK_WEBHOOK; then
  echo "SLACK_WEBHOOK already set"
elif grep -q '^SLACK_WEBHOOK=' ~/github/.env; then
  grep -m1 '^SLACK_WEBHOOK=' ~/github/.env | cut -d= -f2- | tr -d '\r' | gh secret set SLACK_WEBHOOK
else
  echo "SLACK_WEBHOOK not found in ~/github/.env"
fi
```

- The value goes through stdin only. Never echo it, print it, pass it as a command-line argument or put
  it in a file in the repo.
- Never use `gh secret set --env-file ~/github/.env`: that uploads every secret in the file to the repo.
- Never overwrite an existing `SLACK_WEBHOOK` secret unless the user asks; a repo may deliberately post
  to a different channel.
- If the variable is missing from `~/github/.env`, stop and tell the user.

## The notify job

Add this as the last job of the workflow. List every other job in `needs` so it waits for all of them.
It is a template: the user may customise the wording, fields or layout per repo, but keep the colours
and the success, failure and skip rules unless they ask otherwise.

```yaml
  notify:
    needs: [build, deploy]   # every other job in this workflow
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

Why it is built this way:

- **Separate job, not a final step.** A failed step stops the rest of its job, and a step cannot see
  other jobs' results. A `notify` job with `needs` sees every job's outcome, and works the same for
  single-job and multi-job workflows.
- **`!cancelled()`** lets the job run after a failure (the default `success()` would skip it) but not
  after the run is cancelled. `!contains(needs.*.result, 'cancelled')` also skips it when an individual
  job was cancelled.
- **`github.ref == 'refs/heads/main'`** limits notifications to runs on main. Pull request runs use
  `refs/pull/<n>/merge`, so they post nothing, and fork PRs could not read the secret anyway.
- **Skipped jobs count as success.** Only a `failure` result turns the message red.
- **Untrusted values go through `env`.** The commit message and branch name are attacker-controllable
  text; never interpolate `${{ ... }}` expressions for them directly into `run:`. `jq --arg` handles
  JSON escaping.
- **Legacy `attachments`** are the only incoming-webhook format with a coloured side bar; Block Kit has
  no colour.
- **Slack never fails the build.** A missing secret or a failed post is a warning annotation on the run,
  not a failed job.
