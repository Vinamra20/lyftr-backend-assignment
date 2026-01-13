http_requests_total = {}
webhook_requests_total = {}

def inc_http(path, status):
    key = (path, status)
    http_requests_total[key] = http_requests_total.get(key, 0) + 1

def inc_webhook(result):
    webhook_requests_total[result] = webhook_requests_total.get(result, 0) + 1

def render_metrics():
    lines = []

    for (path, status), count in http_requests_total.items():
        lines.append(
            f'http_requests_total{{path="{path}",status="{status}"}} {count}'
        )

    for result, count in webhook_requests_total.items():
        lines.append(
            f'webhook_requests_total{{result="{result}"}} {count}'
        )

    return "\n".join(lines)
