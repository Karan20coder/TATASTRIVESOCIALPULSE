import urllib.request
import json
import re

print("--- 1. Testing HTML Dashboard ---")
html_res = urllib.request.urlopen("http://127.0.0.1:8042/")
html = html_res.read().decode("utf-8")
print(f"Status 200, HTML size: {len(html)} bytes")
has_accordion = "comments-accordion" in html
has_toggle = "comments-toggle-btn" in html
has_items = "comment-item" in html
has_chips = "c-chip" in html
print(f"Contains comments-accordion: {has_accordion}")
print(f"Contains comments-toggle-btn: {has_toggle}")
print(f"Contains comment-item: {has_items}")
print(f"Contains c-chip: {has_chips}")

print("\n--- 2. Testing /api/mentions ---")
api_res = urllib.request.urlopen("http://127.0.0.1:8042/api/mentions?limit=50")
mentions = json.loads(api_res.read().decode("utf-8"))
print(f"Total mentions returned: {len(mentions)}")

with_comments = [m for m in mentions if m.get("analyzed_comments")]
print(f"Mentions with analyzed comments: {len(with_comments)}")

for idx, m in enumerate(with_comments[:3]):
    label = m.get("title") or (m.get("text")[:50] + "...")
    print(f"\n[Mention #{idx+1} ({m['source'].upper()})] {label}")
    print(f"Counts: {m.get('comment_counts')}")
    for c in m["analyzed_comments"]:
        print(f"  [{c['sentiment'].upper()}] {c['author']} ({c['confidence_pct']}% conf): \"{c['text']}\"")
        if c.get("sentiment_reason"):
            print(f"      Evidence: {c['sentiment_reason']}")
