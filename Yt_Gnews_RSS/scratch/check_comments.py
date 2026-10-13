import sqlite3

for db_name in ["socialpulse.db", "harken.db"]:
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    rows = cur.execute("SELECT id, author, text, sentiment, confidence, sentiment_reason, url FROM mentions WHERE record_type = 'comment'").fetchall()
    print(f"{db_name} has {len(rows)} comments:")
    for r in rows:
        safe_t = r[2][:70].encode('ascii', 'backslashreplace').decode('ascii')
        print(f"  [{r[3].upper()}] {r[1]}: {safe_t} (conf: {r[4]})")

