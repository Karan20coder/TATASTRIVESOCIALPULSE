import urllib.request
import re
import sqlite3
from collections import Counter


conn = sqlite3.connect("harken.db")
cur = conn.cursor()
rows = cur.execute("SELECT id, source, query, title, created_at FROM mentions WHERE source IN ('facebook', 'linkedin')").fetchall()
for r in rows:
    print(r)


for url in ["http://127.0.0.1:8042/", "http://127.0.0.1:8042/?q=Tata+STRIVE", "http://127.0.0.1:8042/?q="]:
    html = urllib.request.urlopen(url).read().decode("utf-8")
    feed_sources = re.findall(r'<li class="mention [^"]*" data-record-type="[^"]*" data-source="([^"]+)"', html)
    print(f"URL {url} -> feed count: {len(feed_sources)}, sources: {Counter(feed_sources)}")


all_data_sources = re.findall(r'data-source="([^"]+)"', html)
print("all data-source attributes in html:", Counter(all_data_sources))



