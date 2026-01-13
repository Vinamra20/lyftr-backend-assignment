from app.storage import get_stats
import time
from app.logging_utils import log_request
from app.metrics import inc_http, inc_webhook, render_metrics
from fastapi.responses import PlainTextResponse



from fastapi import Request, Header, HTTPException
from app.storage import insert_message
from fastapi import Query
from app.storage import list_messages

from fastapi import FastAPI, HTTPException
from app.models import init_db
from app.config import DATABASE_URL, WEBHOOK_SECRET
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

import hmac
import hashlib


app = FastAPI()


@app.middleware("http")
async def logging_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    latency_ms = (time.time() - start_time) * 1000

    log_request(
        request=request,
        status=response.status_code,
        latency_ms=latency_ms
    )
    inc_http(request.url.path, response.status_code)

    return response

@app.on_event("startup")
def startup():
    init_db(DATABASE_URL)

@app.get("/health/live")
def live():
    return {"status": "alive"}

@app.get("/health/ready")
def ready():
    if not WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="not ready")
    return {"status": "ready"}

class WebhookMessage(BaseModel):
    message_id: str = Field(..., min_length=1)
    from_: str = Field(..., alias="from")
    to: str
    ts: datetime
    text: Optional[str] = Field(None, max_length=4096)
def verify_signature(secret: str, body: bytes, signature: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)
  
@app.post("/webhook")
async def webhook(
    request: Request,
    x_signature: str = Header(None)
):
    if not WEBHOOK_SECRET:
        raise HTTPException(status_code=503)

    raw_body = await request.body()

    if not x_signature or not verify_signature(WEBHOOK_SECRET, raw_body, x_signature):
        raise HTTPException(status_code=401, detail="invalid signature")

    payload = await request.json()
    WebhookMessage(**payload)

    result = insert_message(DATABASE_URL, payload)

    log_request(
    request=request,
    status=200,
    latency_ms=0,
    extra={
        "message_id": payload["message_id"],
        "dup": result == "duplicate",
        "result": result
    }
)

    return {"status": "ok"}
    inc_webhook(result)


@app.get("/messages")
def get_messages(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    from_: str | None = Query(None, alias="from"),
    since: str | None = None,
    q: str | None = None
):
    data, total = list_messages(
        DATABASE_URL,
        limit,
        offset,
        from_,
        since,
        q
    )

    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/stats")
def stats():
    return get_stats(DATABASE_URL)

@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return render_metrics()
