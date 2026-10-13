"""Tests for Topic Intelligence Engine & API in Tata STRIVE Social Pulse AI."""

from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from harken.models import Mention
from harken.store import Store
from harken.analyze.topic_intelligence import (
    TopicIntelligenceEngine,
    DEFAULT_TOPICS,
    TopicDefinition,
    get_topic_engine,
)
from harken.web.app import create_app


def test_url_normalization():
    engine = TopicIntelligenceEngine()
    
    # Strip tracking parameters
    u1 = "https://economictimes.indiatimes.com/jobs/skilling-india?utm_source=rss&utm_medium=feed"
    u2 = "https://economictimes.indiatimes.com/jobs/skilling-india"
    u3 = "HTTP://EconomicTimes.IndiaTimes.com/jobs/skilling-india/?fbclid=123"
    
    assert engine.normalize_url(u1) == "https://economictimes.indiatimes.com/jobs/skilling-india"
    assert engine.normalize_url(u2) == "https://economictimes.indiatimes.com/jobs/skilling-india"
    assert engine.normalize_url(u3) == "https://economictimes.indiatimes.com/jobs/skilling-india"


def test_headline_fingerprinting():
    engine = TopicIntelligenceEngine()
    
    h1 = "Tata STRIVE Launches New Skill Development Centre in Pune - Times of India"
    h2 = "Tata STRIVE launches new skill development centre in Pune | Mint"
    
    fp1 = engine.fingerprint_headline(h1)
    fp2 = engine.fingerprint_headline(h2)
    
    assert fp1 == fp2
    assert "tatastrivelaunchesnewskilldevelopmentcentrein" in fp1


def test_article_deduplication():
    engine = TopicIntelligenceEngine()
    now = datetime.now(timezone.utc)
    
    m1 = Mention(
        id="m1",
        source="rss",
        query="skill development",
        record_type="article",
        title="Youth Skill Training Drives Jobs in India - Economic Times",
        text="India is expanding vocational skilling across states.",
        url="https://economictimes.com/news/1?utm_source=feed",
        author="Economic Times",
        created_at=now,
    )
    # Duplicate by URL (different params)
    m2 = Mention(
        id="m2",
        source="rss",
        query="skill development",
        record_type="article",
        title="Youth Skill Training Drives Jobs in India",
        text="India is expanding vocational skilling across states.",
        url="https://economictimes.com/news/1?utm_medium=email",
        author="Economic Times",
        created_at=now - timedelta(hours=1),
    )
    # Duplicate by syndicated headline with different url
    m3 = Mention(
        id="m3",
        source="gnews",
        query="vocational training",
        record_type="article",
        title="Youth Skill Training Drives Jobs in India | Wire",
        text="Syndicated copy of the same article.",
        url="https://wire.in/repost/1",
        author="Wire Feed",
        created_at=now - timedelta(hours=2),
    )
    # Unique distinct article
    m4 = Mention(
        id="m4",
        source="rss",
        query="Tata STRIVE",
        record_type="article",
        title="Tata STRIVE Announces Women in Tech Cohort - PTI",
        text="Tata STRIVE has graduated 500 young women in digital skills.",
        url="https://pti.in/tata-strive-tech",
        author="PTI",
        created_at=now - timedelta(hours=3),
    )
    
    mentions = [m1, m2, m3, m4]
    deduped, stats = engine.deduplicate_articles(mentions)
    
    assert stats.total_raw_articles == 4
    assert stats.total_unique_articles == 2
    assert stats.duplicates_removed == 2
    assert len(deduped) == 2


def test_single_primary_category_classification():
    engine = TopicIntelligenceEngine()
    now = datetime.now(timezone.utc)
    
    m_tata = Mention(
        id="1", source="rss", query="Tata STRIVE", record_type="article",
        title="Tata STRIVE and TCIT partner for youth vocational courses",
        text="Details about vocational education and jobs.",
        url="https://example.com/1", author="Media", created_at=now
    )
    m_vocational = Mention(
        id="2", source="rss", query="vocational training", record_type="article",
        title="Modernising ITI centres with hands-on technician apprenticeship",
        text="Vocational education reforms across state polytechnics.",
        url="https://example.com/2", author="Media", created_at=now
    )
    m_digital = Mention(
        id="3", source="rss", query="digital skills", record_type="article",
        title="AI skilling and cloud computing careers for Indian engineering freshers",
        text="Cybersecurity and coding courses see massive demand.",
        url="https://example.com/3", author="Media", created_at=now
    )
    
    cat1 = engine.categorize_article(m_tata)
    cat2 = engine.categorize_article(m_vocational)
    cat3 = engine.categorize_article(m_digital)
    
    assert cat1.key == "tata_strive"
    assert cat2.key == "skill_development"
    assert cat3.key == "digital_skills"


def test_percentages_exact_sum_to_100():
    counts = {
        "tata_strive": 28,
        "other_industry": 28,
        "skill_development": 27,
        "youth_employment": 3,
        "education_training": 2,
        "government_initiatives": 1,
    }
    total = sum(counts.values())  # 89
    
    pcts = TopicIntelligenceEngine.calculate_percentages(counts, total)
    total_pct = round(sum(pcts.values()), 1)
    
    assert total_pct == 100.0
    for k, v in pcts.items():
        assert 0.0 <= v <= 100.0


def test_transparent_priority_score_calculation():
    engine = TopicIntelligenceEngine()
    now = datetime.now(timezone.utc)
    tata_topic = next(t for t in DEFAULT_TOPICS if t.key == "tata_strive")
    
    # Create sample articles across distinct publishers
    articles = [
        Mention(id=f"a{i}", source="rss", query="Tata STRIVE", record_type="article",
                title=f"Tata STRIVE story {i}", text="Tata STRIVE news",
                url=f"https://pub{i}.com/tata", author=f"Publisher {i}",
                created_at=now - timedelta(days=i))
        for i in range(10)
    ]
    
    score, momentum_label, badge = engine.calculate_priority_score(
        topic=tata_topic,
        articles=articles,
        total_unique_articles=20,
        max_topic_count=10,
        total_publishers_across_corpus=10,
    )
    
    assert 50 <= score <= 100
    assert momentum_label in {"Accelerating", "Consistent", "Steady", "Cooling", "Baseline"}
    assert badge in {"positive", "neutral", "negative"}


def test_real_database_analysis():
    store = Store("socialpulse.db")
    try:
        mentions = store.mentions(limit=1000)
        engine = get_topic_engine()
        res = engine.analyze(mentions, date_range="all")
        
        # Verify deduplication stats on real data
        assert res.deduplication.total_raw_articles > 0
        assert res.deduplication.total_unique_articles > 0
        assert res.summary_cards["total_unique"] == res.deduplication.total_unique_articles
        assert res.summary_cards["distinct_topics"] > 0
        
        # Verify percentages sum
        total_share = round(sum(s["percentage_share"] for s in res.segments), 1)
        assert total_share == 100.0
        
        # Verify priority rankings
        assert len(res.priority_topics) > 0
        top_ranked = res.priority_topics[0]
        assert "priority_score" in top_ranked
        assert top_ranked["priority_score"] > 0
        
        # Verify time series
        assert len(res.time_series) > 0
        
        # Verify recommendations cite real URLs
        for rec in res.recommendations:
            assert "evidence_url" in rec
            assert len(rec["evidence_url"]) > 0
    finally:
        store.close()


def test_api_generate_topic_intelligence_endpoint():
    app = create_app(db_path="socialpulse.db")
    client = TestClient(app)
    
    # POST endpoint
    res = client.post("/api/news/topic-intelligence/generate", json={"range": "all"})
    assert res.status_code == 200
    data = res.json()
    
    assert "summary_cards" in data
    assert "segments" in data
    assert "priority_topics" in data
    assert "deduplication" in data
    assert data["deduplication"]["total_unique_articles"] > 0
    
    # GET endpoint
    res_get = client.get("/api/news/topic-intelligence?range=all")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["summary_cards"]["total_unique"] == data["summary_cards"]["total_unique"]
