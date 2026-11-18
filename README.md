 # Expense Tracker API

A containerised Flask API with a SQLite store — provisioned on AWS EC2 with Terraform, configured with Ansible, and deployed continuously: every push is tested (pytest), built into a Docker image, scanned for vulnerabilities (Trivy), then — after a manual approval — deployed to the server by a self-hosted GitHub Actions runner and verified with an HTTPS health check. Served over nginx with a Let's Encrypt certificate.

## Pipeline

git push → pytest → Docker image built & pushed to GHCR → Trivy scan → manual approval (GitHub environment: production) → deployed on the server (git pull, docker compose up --build) → health check

![CI](https://github.com/hadyatotakhail08-web/expense-tracker/actions/workflows/ci.yml/badge.svg)


