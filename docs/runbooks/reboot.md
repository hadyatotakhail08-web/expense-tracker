```markdown
# Runbook: The server rebooted (cold start)

**Use this when:** EC2 restarted on purpose (to save money) or AWS rebooted
it for maintenance. Find out what came back and what needs a human.

## The 60-second sweep (run on the server)

	sudo systemctl status actions.runner-svc.service
	sudo docker compose ps -a        # from /opt/expense-tracker
	curl -f https://app.thehimma.com/health

Expected: runner active, all five containers Up, health endpoint ok.
It's all self-healing by design: the runner runs as a systemd service,
and Docker restarts the compose containers when the daemon starts.

## The two things that need a human

1. The public IP can change on stop/start. If the domain stops working,
   update the app.thehimma.com DNS record to the new EC2 public IP.
2. SSH only works from the home wifi (IP allow-list on the security group).
```
