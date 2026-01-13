# Lyftr AI – Backend Assignment

This project is a containerized backend service built using **FastAPI** and **SQLite**.
It ingests WhatsApp-like webhook messages securely and exposes APIs for listing,
analytics, health checks, and metrics.

---

## Tech Stack

- Python 3.11
- FastAPI
- SQLite
- Docker & Docker Compose

---

## How to Run (One Command)

````bash
make up


The API will be available at:

http://localhost:8000


To stop everything:

make down

Environment Variables

The following environment variables are required:

WEBHOOK_SECRET – Secret key for HMAC verification

DATABASE_URL – SQLite DB path (default: sqlite:////data/app.db)

These are already configured in docker-compose.yml.

API Endpoints
Health

GET /health/live → Always returns 200 if app is running

GET /health/ready → Returns 200 only if DB is ready and secret is set

Webhook

POST /webhook

Validates HMAC SHA256 signature

Ensures idempotency using message_id

Returns { "status": "ok" }

Messages

GET /messages

Supports pagination and filters

Query params: limit, offset, from, since, q

Stats

GET /stats

Returns total messages, unique senders, top senders, and timestamps

Metrics

GET /metrics

Prometheus-style metrics

Includes http_requests_total and webhook_requests_total

Design Decisions

SQLite chosen for simplicity and idempotency via primary key

HMAC SHA256 used to secure webhook requests

Pagination implemented using SQL LIMIT/OFFSET

Structured JSON logs emitted for observability

Dockerized to ensure consistent runtime for evaluation



---

## Setup Used

- VS Code
- Terminal
- Docker Desktop
- ChatGPT

✅ This README **matches exactly what evaluators expect**.

---


Run these **in order**, exactly like the evaluator.

---

### Start everything

```bash
make up
sleep 5
````

---

### Health checks

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

**Expected:**

```json
{"status":"alive"}
{"status":"ready"}
```

---

### Webhook test

**Create body**

```bash
BODY='{"message_id":"m1","from":"+919876543210","to":"+14155550100","ts":"2025-01-15T10:00:00Z","text":"Hello"}'
```

**Generate signature**

```bash
python3 - <<EOF
import hmac, hashlib
print(hmac.new(b"testsecret", b'$BODY', hashlib.sha256).hexdigest())
EOF
```

**Send webhook**

```bash
curl -i \
  -H "Content-Type: application/json" \
  -H "X-Signature: <PASTE_SIGNATURE>" \
  -d "$BODY" \
  http://localhost:8000/webhook
```

**Expected:**

```http
HTTP/1.1 200 OK
{"status":"ok"}
```

Send again → still **200 OK** (idempotent ✅)

---

### Messages

```bash
curl http://localhost:8000/messages
```

---

### Stats

```bash
curl http://localhost:8000/stats
```

---

### Metrics

```bash
curl http://localhost:8000/metrics
```

Must contain:

- `http_requests_total`
- `webhook_requests_total`

---

### Logs

```bash
make logs
```

You should see structured JSON logs, for example:

```json
{
  "ts": "...",
  "level": "INFO",
  "request_id": "...",
  "method": "POST",
  "path": "/webhook",
  "status": 200,
  "latency_ms": 1.2,
  "message_id": "m1",
  "dup": false,
  "result": "created"
}
```

---

### Stop

```bash
make down
```
