# Expense Tracker — a real app, running like a real business

I built a small Flask web app for tracking expenses, then did everything a company would need to run it properly: deployed it to AWS, automated every release, secured it, watched it with dashboards and alerts, and kept the monthly bill under control. It runs live today, and I monitor and maintain it myself.

**Try it:** https://app.thehimma.com/health

The infrastructure is defined in [expense-tracker-infra](https://github.com/hadyatotakhail08-web/expense-tracker-infra) and the server setup is automated in [expense-tracker-ansible](https://github.com/hadyatotakhail08-web/expense-tracker-ansible).

## Why I built it this way

Most learning projects run once on a laptop and stop. I wanted the opposite: one realistic app, taken through every stage a DevOps engineer actually deals with at work — real costs, real users, real incidents. Real systems fail in ways tutorials don't. When something breaks, I find out from my own monitoring, diagnose it, fix it in code, and write down what I learned. That loop is the whole point.

## How it all fits together

### The pipeline: what happens when I push code

| Step | What happens | Where |
| --- | --- | --- |
| 1 | I push code to `main` | my laptop |
| 2 | Tests run (pytest) | GitHub Actions |
| 3 | Docker image is built and scanned for vulnerabilities (Trivy) | GitHub Actions |
| 4 | Image is pushed to GitHub Container Registry | GitHub Actions |
| 5 | Deploy waits for my approval | GitHub "production" environment |
| 6 | Server pulls the new code and rebuilds the app | my EC2 server |
| 7 | Health check confirms the app answers at /health | the pipeline, automatically |

If any step fails, the pipeline stops and nothing reaches the server.

### The monitoring: what happens while it runs

| Piece | What it does | Where |
| --- | --- | --- |
| App metrics | counts requests and measures response time (I added this to the Flask code) | port 9200 |
| Node Exporter | reports server stats (CPU, memory, disk) | port 9100 |
| Prometheus | collects all these numbers every 15 seconds | port 9090 |
| Grafana | turns them into dashboards | port 3000 |
| Alertmanager | emails me when something is wrong (FIRING) and when it recovers (RESOLVED) | port 9093 |

What each piece means, for anyone reading who isn't an engineer:

- **Flask** — a small Python web framework. The app is an API that stores expenses in a database and answers requests.
- **Docker** — packages the app with everything it needs, so it runs the same on my laptop and on the server.
- **GitHub Actions** — the automated assembly line. Every push runs the same steps: tests, build, scan, deploy.
- **Terraform** — describes the AWS infrastructure (server, firewall rules, permissions) in files, so it can be rebuilt exactly.
- **Prometheus / Grafana / Alertmanager** — the monitoring stack. Prometheus collects numbers (requests, latency), Grafana turns them into dashboards, Alertmanager emails me when something is wrong and when it recovers.

| Layer | Technology |
| --- | --- |
| App | Python 3.12, Flask, SQLite |
| Containers | Docker, Docker Compose (5 services) |
| CI/CD | GitHub Actions — test → build → deploy with human approval gate |
| Infra | AWS EC2 (eu-west-2), written in Terraform |
| Security | least-privilege IAM, Secrets Manager, Trivy scans |
| Monitoring | Prometheus, Grafana, Alertmanager → email alerts |

## The journey, stage by stage

### Stage 1 — The app itself

A Flask API with SQLite (a simple database stored in a file). Endpoints to add and list expenses, plus a `/health` endpoint that answers "ok" when the app is alive — that endpoint is what my pipeline and monitoring use to check the app is actually working.

### Stage 2 — A real server

The app went from my laptop to an Ubuntu server on AWS EC2. nginx sits in front of it, taking requests from the internet and passing them to the app, and the app runs as a systemd service so Linux itself restarts it if it crashes or the server reboots. I proved it survives both: a stop/start test and a full reboot test.

What tripped me up: systemd kept failing with `error 203/EXEC` because the paths in my service file pointed to a virtual environment folder that didn't match where the code actually lived. Linux errors describe the symptom — finding the real cause taught me to diagnose, not just read the error.

### Stage 3 — The infrastructure as code

The server, firewall rules and permissions were rebuilt in Terraform. State is stored in S3 with locking, so two runs can't corrupt the setup at the same time. There's a dev and a prod environment, and an AWS budget that emails me at 80% of $10/month — I pay for this myself, so cost is not theoretical. I tested drift detection on purpose: changed things outside Terraform, watched `terraform plan` flag them, and `terraform apply` put everything back in line.

### Stage 4 — Automated server setup

Ansible playbooks turn a fresh Ubuntu server into a fully configured expense-tracker server. Proven idempotent (second run: zero changes) and self-healing (deleted a config by hand, rerun repaired only that). Full story in the Ansible repo.

### Stage 5 — Continuous deployment

Every push to `main` runs the pipeline in the table above. Two details I'm proud of:

- **Nothing deploys without my approval.** The deploy job points at GitHub's "production" environment, which requires a reviewer — me. Making it a team is a one-line change.
- **Green means the app answers.** After deploying, the pipeline curls `https://app.thehimma.com/health` and fails if there's no response. I learned this the hard way: an earlier health check hit the wrong URL and returned 404 while looking correct.

### Stage 6 — Security

- HTTPS via Let's Encrypt, with permanent redirects from HTTP
- SSH open only to my home IP
- Credentials in AWS Secrets Manager, never in files
- A Trivy vulnerability scan on the Docker image at every build
- During this hardening I discovered Gmail app passwords had been committed to git history. I rotated the password first (rotation beats scrubbing), rewrote the history, then moved the live config out of git into a template plus a gitignored file.

### Stage 7 — Monitoring and alerting

Prometheus scrapes both the app (I added request-count and request-latency metrics to the Flask code myself) and Node Exporter (server stats). Grafana shows it on dashboards. Alertmanager emails me. I didn't believe it worked until I'd fired every kind of alert:

- Deliberate outage test: `docker compose stop app` → alert pending for 2 minutes → FIRING email arrives → restart → RESOLVED email arrives. Timed and verified end to end.
- Discovered `send_resolved` defaults to off, meaning recovery emails are silently dropped unless explicitly enabled. An observability gap you only find by testing both directions.

## Real incidents (each with a fix committed in code)

1. **Locked out by my own security rule.** SSH allows only my home IP. My home IP changed overnight, so I was locked out — the rule working exactly as designed. I started using the deploy job as a second route to reach the server. Lesson: restrictive rules are right, but plan the escape route before you need it.
2. **Docker kept serving old code.** A named volume was shadowing the app's code folder. Docker only seeds a named volume from the image when the volume is first created — so no rebuild ever reached the running container. It looked up to date but silently ran the old version. Lesson: verify what's inside the container, not what should be.
3. **nginx "running" but serving nothing.** After a config repair, `systemctl status` showed green but listening sockets showed nothing on 443 — the process was alive with stale state. Fixed the playbook to restart the service after config changes. Lesson: a live process is not a working service; prove it with a real request.
4. **YAML indentation and the paste buffer.** Several pipeline failures came from pasting blocks at the wrong indentation or mixing tabs and spaces — one job ended up nested inside another. Habit formed: write config in an editor with spaces, read the whole file back before committing.

## Cost

The whole platform runs on roughly the cost of one meal a month, because of choices, not luck: a small instance, a $10 budget with an email alert at 80%, resources tagged for cost tracking, the server stopped when not in use, and one forgotten dev instance that quietly billed for a month — my own lesson that a budget needs a monthly console check alongside it.

## What's next

- Fix the docker volume layout (structural solution to incident 2)
- Migrate to Kubernetes (EKS) and add GitOps with ArgoCD
- Backups and restore drills
- More incident drills, each with a short written postmortem
- Move monitoring off the app server, so the dashboards survive the app server dying (external heartbeat first)
- Write the operations manual: deploy/rollback steps, AppDown response, database backup and restore, cold start after a reboot, monthly cost check

## Run it locally


The app runs on port 5050. (Fun fact: not 5000, because on a Mac that port is taken by AirPlay — my first encounter with "the port is already in use for a reason you'd never guess".)

## The other repos in this platform

- [expense-tracker-infra](https://github.com/hadyatotakhail08-web/expense-tracker-infra) — the Terraform infrastructure
- [expense-tracker-ansible](https://github.com/hadyatotakhail08-web/expense-tracker-ansible) — the Ansible server automation
