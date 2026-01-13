import sqlite3
from datetime import datetime

def insert_message(db_path, payload):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)
        """, (
            payload["message_id"],
            payload["from"],
            payload["to"],
            payload["ts"],
            payload.get("text"),
            datetime.utcnow().isoformat() + "Z"
        ))
        conn.commit()
        return "created"
    except sqlite3.IntegrityError:
        return "duplicate"
    finally:
        conn.close()
        
def list_messages(db_path, limit, offset, from_filter, since, q):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    where_clauses = []
    params = []

    if from_filter:
        where_clauses.append("from_msisdn = ?")
        params.append(from_filter)

    if since:
        where_clauses.append("ts >= ?")
        params.append(since)

    if q:
        where_clauses.append("LOWER(text) LIKE ?")
        params.append(f"%{q.lower()}%")

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    # total count (without limit/offset)
    cursor.execute(
        f"SELECT COUNT(*) FROM messages {where_sql}",
        params
    )
    total = cursor.fetchone()[0]

    # fetch paginated rows
    cursor.execute(
        f"""
        SELECT message_id, from_msisdn, to_msisdn, ts, text
        FROM messages
        {where_sql}
        ORDER BY ts ASC, message_id ASC
        LIMIT ? OFFSET ?
        """,
        params + [limit, offset]
    )

    rows = cursor.fetchall()
    conn.close()

    data = []
    for r in rows:
        data.append({
            "message_id": r[0],
            "from": r[1],
            "to": r[2],
            "ts": r[3],
            "text": r[4]
        })

    return data, total

def get_stats(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # total messages
    cursor.execute("SELECT COUNT(*) FROM messages")
    total_messages = cursor.fetchone()[0]

    # unique senders
    cursor.execute("SELECT COUNT(DISTINCT from_msisdn) FROM messages")
    senders_count = cursor.fetchone()[0]

    # top senders (max 10)
    cursor.execute("""
        SELECT from_msisdn, COUNT(*) as cnt
        FROM messages
        GROUP BY from_msisdn
        ORDER BY cnt DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()

    messages_per_sender = []
    for r in rows:
        messages_per_sender.append({
            "from": r[0],
            "count": r[1]
        })

    # first and last timestamps
    cursor.execute("SELECT MIN(ts), MAX(ts) FROM messages")
    first_ts, last_ts = cursor.fetchone()

    conn.close()

    return {
        "total_messages": total_messages,
        "senders_count": senders_count,
        "messages_per_sender": messages_per_sender,
        "first_message_ts": first_ts,
        "last_message_ts": last_ts
    }
