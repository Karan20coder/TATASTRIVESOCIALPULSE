import json
import urllib.request

req = urllib.request.Request("http://127.0.0.1:8042/api/news/topic-intelligence")
res = urllib.request.urlopen(req)
data = json.loads(res.read().decode("utf-8"))

print("=== TOPIC INTELLIGENCE SUMMARY ===")
print("Raw articles collected:", data["deduplication"]["total_raw_articles"])
print("Unique deduplicated articles:", data["deduplication"]["total_unique_articles"])
print("Syndicated duplicates removed:", data["deduplication"]["duplicates_removed"])
print("Unique publishers:", data["deduplication"]["unique_publishers_count"])
print("Deduplication method:", data["deduplication"]["deduplication_method"])
print("Limitations note:", data["deduplication"]["limitations_note"])

print("\n=== SUMMARY CARDS ===")
for k, v in data["summary_cards"].items():
    print(f"  {k}: {v}")

print("\n=== TOPIC BREAKDOWN (PIE SEGMENTS) ===")
for s in data["segments"]:
    print(f"  • {s['name']}: {s['count']} articles ({s['share']}%) [Color: {s['color']}]")

print("\n=== TOPIC PRIORITY RANKINGS ===")
for i, p in enumerate(data["priority_topics"], 1):
    print(f"  #{i} {p['topic']}: Priority Score {p['priority_score']}/100 | Momentum: {p['momentum_label']} | Relevance: {p['relevance_score']}% | Outlets: {p['publisher_count']}")

print("\n=== AI STRATEGIC RECOMMENDATIONS ===")
for r in data["recommendations"]:
    print(f"  • Topic: {r['topic']} (Score {r['priority_score']})")
    print(f"    Campaign Idea: {r['campaign_idea']}")
    print(f"    Objective: {r['communication_objective']}")
    print(f"    Audience: {r['target_audience']}")
    print(f"    Hashtags: {' '.join(r['suggested_hashtags'])}")
    print(f"    Evidence: \"{r['evidence_headline']}\" via {r['evidence_publisher']}")
    print(f"    URL: {r['evidence_url']}")
