"""Comprehensive automated tests for Social Pulse AI components and API contracts."""

import re
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from harken.models import Mention, Sentiment
from harken.store import Store
from harken.config import Config
from harken.sources.rss import RSSSource
from harken.sources.youtube import YouTubeSource
from harken.sources.gnews import GNewsSource
from harken.sources.instagram import InstagramSource
from harken.analyze.classifier import ContentClassifier, CATEGORIES
from harken.analyze.trends import TrendEngine
from harken.analyze.questions import QuestionDiscoverer
from harken.analyze.copilot import CampaignCopilot
from harken.web.app import create_app
from fastapi.testclient import TestClient


def test_classifier_and_sentiment_contract():
    classifier = ContentClassifier()
    now = datetime.now(timezone.utc)
    
    # Positive brand and vocational training mention
    m_pos = Mention(
        id="m-test-1",
        source="youtube",
        query="Tata STRIVE Programmes",
        author="Trainer",
        title="Tata STRIVE youth digital training",
        text="Tata STRIVE is doing exceptional work training youth in digital skills and helping freshers get certified jobs.",
        url="https://youtube.com/watch?v=mock1",
        created_at=now,
        sentiment=Sentiment.POSITIVE,
    )
    result_pos = classifier.classify(m_pos)
    
    assert result_pos.category in CATEGORIES
    assert result_pos.confidence >= 0.7
    assert "positive" in result_pos.sentiment_reason.lower() or "satisfaction" in result_pos.sentiment_reason.lower()

    # Negative complaint mention
    m_neg = Mention(
        id="m-test-2",
        source="youtube",
        query="Vocational & Technical Training",
        author="Student",
        title="Certificate Issue",
        text="Terrible delay in certificate distribution. No proper response or placement support from the centre.",
        url="https://youtube.com/watch?v=mock2",
        created_at=now,
        sentiment=Sentiment.NEGATIVE,
    )
    result_neg = classifier.classify(m_neg)
    assert result_neg.category in CATEGORIES
    assert "complaint" in result_neg.sentiment_reason.lower() or "delay" in result_neg.sentiment_reason.lower() or "frustration" in result_neg.sentiment_reason.lower()


def test_trend_engine_velocity():
    engine = TrendEngine()
    now = datetime.now(timezone.utc)
    
    # Create synthetic mentions: heavy recent volume to test rising/emerging trend
    mentions = [
        Mention(
            id=f"yt-{i}",
            source="youtube",
            query="Digital Skills",
            author="Trainer",
            title=f"AI Skilling in 2026 #{i}",
            text="Digital skill development for youth employability",
            url=f"https://youtube.com/watch?v=mock{i}",
            created_at=now,
            category="Digital Skills & Job Readiness",
            sentiment=Sentiment.POSITIVE,
        )
        for i in range(10)
    ]
    
    trends = engine.analyze(mentions)
    assert len(trends) > 0
    top_trend = trends[0]
    assert top_trend.topic == "Digital Skills & Job Readiness"
    assert top_trend.total_records == 10
    assert top_trend.recent_count == 10
    assert top_trend.label in {"emerging", "rising"}
    assert top_trend.velocity > 1.0


def test_question_discoverer_clustering():
    discoverer = QuestionDiscoverer()
    now = datetime.now(timezone.utc)
    mentions = [
        Mention(
            id="comm-1",
            source="youtube",
            query="Tata STRIVE",
            author="Student",
            title=None,
            text="How can I apply for this course? What is the fee structure and eligibility?",
            url="https://youtube.com/watch?v=abc",
            created_at=now,
            record_type="comment",
            category="Tata STRIVE Programmes",
        ),
        Mention(
            id="comm-2",
            source="youtube",
            query="Tata STRIVE",
            author="Learner",
            title=None,
            text="Where is the nearest training centre in Pune? Is hostel facility provided?",
            url="https://youtube.com/watch?v=xyz",
            created_at=now,
            record_type="comment",
            category="Tata STRIVE Programmes",
        )
    ]
    
    themes = discoverer.discover(mentions)
    assert len(themes) > 0
    fees_theme = next((t for t in themes if "Admission" in t.title or "Eligibility" in t.title), None)
    assert fees_theme is not None
    assert fees_theme.count >= 1
    assert "comm-1" in fees_theme.supporting_mention_ids


def test_campaign_copilot_generation():
    copilot = CampaignCopilot()
    now = datetime.now(timezone.utc)
    mentions = [
        Mention(
            id="art-1",
            source="rss",
            query="Youth employment",
            author="The Hindu",
            title="Industry demands skilling over degrees for freshers",
            text="Vocational training programmes prepare freshers with hands-on labs",
            url="https://example.com/article-1",
            created_at=now,
            category="Youth Employment & Careers",
        )
    ]
    
    brief = copilot.generate_brief(
        topic="Youth Employment & Careers",
        mentions=mentions,
        audience_question="How to get hired as a fresher?",
    )
    
    assert brief.campaign_title is not None
    assert len(brief.carousel_outline) == 5
    assert "hook_0_5s" in brief.short_video_concept or "hook" in str(brief.short_video_concept).lower()
    assert "TataSTRIVE" in brief.caption or "Tata STRIVE" in brief.caption
    assert "verification" in brief.verification_guardrail.lower()
    assert len(brief.supporting_urls) > 0


def test_store_persistence_and_alerts(tmp_path):
    db_file = str(tmp_path / "test_sp.db")
    db = Store(db_file)
    
    # Save campaign draft
    draft_data = {
        "title": "Employability 2026",
        "topic": "Digital Skills",
        "platform": "Instagram",
        "status": "draft",
        "objective": "Promote AI skilling",
        "carousel_outline": "Slide 1, Slide 2",
        "video_concept": "Reel hook",
        "caption": "Join Tata STRIVE",
        "cta": "Link in bio",
        "supporting_urls": ["https://example.com"],
    }
    saved = db.save_campaign_draft(draft_data)
    assert saved["id"] is not None
    assert saved["title"] == "Employability 2026"
    
    # Read campaign drafts
    drafts = db.campaign_drafts()
    assert len(drafts) == 1
    assert drafts[0]["id"] == saved["id"]
    
    # Update status
    draft_data["id"] = saved["id"]
    draft_data["status"] = "approved"
    updated = db.save_campaign_draft(draft_data)
    assert updated["status"] == "approved"
    
    # Save & resolve reputation alert
    alert_data = {
        "alert_type": "negative_spike",
        "severity": "warning",
        "title": "Unanswered Queries",
        "reason": "10 questions detected without responses",
        "affected_source": "youtube",
        "time_window": "24h",
        "supporting_urls": ["https://youtube.com/watch?v=123"],
        "suggested_action": "Publish FAQ carousel",
    }
    alert_id = db.save_reputation_alert(alert_data)
    assert isinstance(alert_id, int)
    assert alert_id > 0
    
    active_alerts = db.reputation_alerts(status="active")
    assert len(active_alerts) == 1
    assert active_alerts[0]["id"] == alert_id
    
    resolved = db.resolve_reputation_alert(alert_id)
    assert resolved is True
    assert len(db.reputation_alerts(status="active")) == 0
    
    # Record ingestion run
    run_id = db.record_ingestion_run("youtube", 10, 5, "success")
    assert isinstance(run_id, int)
    last_runs = db.last_ingestion_runs(limit=5)
    assert len(last_runs) == 1
    assert last_runs[0]["source"] == "youtube"
    
    db.close()


def test_dashboard_api_routes(tmp_path):
    db_file = str(tmp_path / "test_api.db")
    db = Store(db_file)
    now = datetime.now(timezone.utc)
    
    # Seed sample mentions
    db.upsert([
        Mention(
            id="m-1",
            source="rss",
            query="Tata STRIVE",
            author="Financial Express",
            title="Tata STRIVE signs new skilling MoU",
            text="Expanding youth skilling initiatives in digital manufacturing",
            url="https://example.com/mou",
            created_at=now,
            record_type="article",
            category="Tata STRIVE Programmes",
            sentiment=Sentiment.POSITIVE,
        ),
        Mention(
            id="m-2",
            source="youtube",
            query="Tata STRIVE",
            author="TechReviewer",
            title="Vocational Skills Roadmap",
            text="Overview of hospitality and technical skilling courses",
            url="https://youtube.com/watch?v=road",
            created_at=now,
            record_type="video",
            views=15000,
            likes=420,
            comments_count=35,
            category="Vocational & Technical Training",
            sentiment=Sentiment.NEUTRAL,
        )
    ])
    db.close()

    app = create_app(db_path=db_file)
    client = TestClient(app)

    # 1. Main Dashboard & CSRF token retrieval
    r_dash = client.get("/")
    assert r_dash.status_code == 200
    assert "Social Pulse AI" in r_dash.text
    match = re.search(r'data-csrf="([^"]+)"', r_dash.text)
    csrf_token = match.group(1) if match else ""
    assert csrf_token != ""

    # 2. News API
    r_news = client.get("/api/news")
    assert r_news.status_code == 200
    news_data = r_news.json()
    assert len(news_data) >= 1
    assert news_data[0]["source"] == "rss"

    # 3. Trends API
    r_trends = client.get("/api/trends")
    assert r_trends.status_code == 200
    assert len(r_trends.json()) > 0

    # 4. Questions API
    r_q = client.get("/api/questions")
    assert r_q.status_code == 200

    # 5. Connectors API
    r_conn = client.get("/api/connectors")
    assert r_conn.status_code == 200
    conn_list = r_conn.json()
    assert any(c["name"] == "youtube" for c in conn_list)
    assert any(c["name"] == "rss" for c in conn_list)

    # 6. Mentions API with query filters
    r_mentions = client.get("/api/mentions?record_type=video")
    assert r_mentions.status_code == 200
    vids = r_mentions.json()
    assert len(vids) == 1
    assert vids[0]["views"] == 15000

    # 7. Copilot generate contract with CSRF token
    r_copilot = client.post(
        "/api/copilot/generate",
        headers={"X-Harken-CSRF": csrf_token},
        json={"topic": "Tata STRIVE Programmes"},
    )
    assert r_copilot.status_code == 200
    cop_data = r_copilot.json()
    assert "campaign_title" in cop_data
    assert "carousel_outline" in cop_data
