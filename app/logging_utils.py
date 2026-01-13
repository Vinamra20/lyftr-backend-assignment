import json
import uuid
from datetime import datetime

def log_request(request, status, latency_ms, extra=None):
    log = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "level": "INFO",
        "request_id": str(uuid.uuid4()),
        "method": request.method,
        "path": request.url.path,
        "status": status,
        "latency_ms": round(latency_ms, 2),
    }

    if extra:
        log.update(extra)

    print(json.dumps(log))
