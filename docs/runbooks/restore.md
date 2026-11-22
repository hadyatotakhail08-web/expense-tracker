```markdown
# Runbook: Backup and restore the SQLite database

**Use this when:** saving the data before risky work, or restoring after disaster.

**Where the data lives:** inside the Docker volume `expense-data`, which is
mounted at `/app` in the app container. The database file is `DB-FILE`.

## Backup (copy OUT of the container, onto the server)

Run on the server:

```sh
sudo docker cp expense-tracker-app-1:/app/DB-FILE ~/expense-backup-$(date +%F).db
```

`$(date +%F)` inserts today's date, so every backup is a new file —
automatic versioning. Verify it's real (not 0 bytes):

```sh
ls -la ~/expense-backup-*
```

## Restore (copy INTO the container)

STOP the app first — copying a database while the app writes to it can
corrupt it:

```sh
sudo docker compose stop app
sudo docker cp ~/expense-backup-YYYY-MM-DD.db expense-tracker-app-1:/app/DB-FILE
sudo docker compose start app
curl -f https://app.thehimma.com/health
```

## Honest limits (interviewers love this section)

Backups stored on the same server protect against *software* mistakes,
not against the server dying. Real next step: copy to S3
(`aws s3 cp ~/expense-backup-<date>.db s3://<backup-bucket>/`), costs pennies.
```
