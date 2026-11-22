# Runbook: Deploying the expense tracker

**Use this when:** you need to ship a change to production, or a deploy failed.

## How a deploy works

git push (Mac) → GitHub Actions runs tests → builds the Docker image →
pushes it to GHCR → a human approves the Production environment →
the self-hosted runner on the server pulls the code and runs
`docker compose up -d --build` → the pipeline curls /health to prove
the app is alive. Nothing deploys without a human click.

## Ship a change

1. Edit code in VS Code. Save (⌘S, dot must vanish).
2. Mac terminal: `git add -A && git commit -m "what changed" && git push`
3. Repo → Actions tab → watch the run → click Approve if the 🟡 appears.
4. Verify: `curl -f https://app.thehimma.com/health` → `{"status":"ok"}`

## Rollback to the last good version

Mac terminal (do NOT do this now — it's the emergency recipe):

		git log --oneline -5          # find the last good commit hash
		git revert <bad-commit-hash>  # creates an inverse commit
		git push

Then approve the 🟡 like any deploy. Why revert and not reset: revert
adds a new commit that undoes the bad one — safe on shared branches;
reset rewrites history and is only for branches nobody else uses.

## Known traps

- "nothing to commit, working tree clean" = the file was never saved (● dot).
- A deploy runs `up -d`, which restarts stopped containers — a deliberate
	test outage gets "healed" by any deploy.
- "failed to connect to the docker API /Users/hadyat/..." = the command
	ran on the Mac; it belongs on the server.
