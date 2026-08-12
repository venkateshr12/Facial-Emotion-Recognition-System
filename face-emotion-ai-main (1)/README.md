# face-emotion-ai

## Session recording API (for invisible background emotion capture)

This project supports starting a background session that samples webcam frames, runs emotion inference, and stores a timestamped JSON report in `recordings/`.

Endpoints:

- POST `/sessions/start`  — start a session. JSON body (optional):
	- `duration` (seconds) default: 600 (10 minutes)
	- `interval` (seconds) default: 1.0
	Response: `{ok: true, id: "<session id>", meta: {...}}`

- POST `/sessions/stop` — stop a running session. JSON body: `{id: "<session id>"}`

- GET `/sessions` — list known sessions and statuses

- GET `/sessions/<id>/report` — fetch the raw recorded JSON report

- GET `/sessions/<id>/summary` — fetch a summarized report (counts, percentages, per-minute buckets)

- GET `/sessions/<id>/download` — download the JSON report file

Reports are stored under `recordings/<id>.json` and contain `meta` and `data` arrays of timestamped records. Use these endpoints to capture user emotions invisibly on the device and upload/store/report from the backend as needed by your app.

Example (PowerShell):

```powershell
# start a 10 minute session (default)
curl -X POST -H "Content-Type: application/json" -d '{"duration":600, "interval":1}' http://127.0.0.1:5000/sessions/start | ConvertFrom-Json

# stop a session
curl -X POST -H "Content-Type: application/json" -d '{"id":"<session id>"}' http://127.0.0.1:5000/sessions/stop

# get summary
curl http://127.0.0.1:5000/sessions/<session id>/summary
```

Security note: Do not run unattended capture in production without clear user consent and appropriate data protections. Consider adding authentication and encryption for API access and storage.

# face-emotion-ai
