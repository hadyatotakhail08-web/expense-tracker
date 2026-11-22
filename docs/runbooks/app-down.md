# Runbook: AppDown alert fired

**Use this when:** Alertmanager emails [FIRING] AppDown — Prometheus has
failed to scrape the app on port 9200 for 2+ minutes.

**What it means:** the formula up{job="expense-app"} == 0 became true —
Prometheus cannot reach the app's metrics page. Usually the container
is stopped or crashed.

## Triage ladder (server, ~30 seconds per step, in order)

Step 1 — Is the container running?

    cd /opt/expense-tracker && sudo docker compose ps -a

    app ... Exited → go to Step 2.
    app ... Up → go to Step 3.

Step 2 — Why did it die?

    sudo docker compose logs app --tail=30

    A Python traceback names the bug.
    "Killed" = out of memory (check dmesg | tail).

Step 3 — Is the metrics port answering?

    sudo docker compose exec app curl -s http://localhost:9200/metrics | head -c 60

    Output starting with # HELP → app is fine; the alert self-resolves.
    Connection refused → restart the app:

    sudo docker compose start app

Step 4 — Verify the fix end to end

    curl -f https://app.thehimma.com/health

    Then watch http://localhost:9090/alerts (via SSH tunnel).
    A [RESOLVED] email follows within ~5 minutes.

## Escalation rule

If the fix isn't obvious in 15 minutes: screenshot the logs, write down
what you tried, and ask for help. A runbook makes the first 15 minutes
effective — it doesn't replace judgement.
