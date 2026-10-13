"""Unit tests for connectors, error handling, and failure states."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import os
import httpx
import pytest

from harken.sources.youtube import YouTubeSource
from harken.sources.rss import RSSSource
from harken.sources.gnews import GNewsSource
from harken.sources.hackernews import HackerNewsSource
from harken.sources.bluesky import BlueskySource
from harken.sources.instagram import InstagramSource


def test_youtube_missing_credentials():
    with patch.dict(os.environ, {"YOUTUBE_API_KEY": "", "HARKEN_YOUTUBE_API_KEY": ""}):
        yt = YouTubeSource(api_key="")
        with pytest.raises(RuntimeError) as exc_info:
            yt.fetch("Tata STRIVE")
        assert "requires YOUTUBE_API_KEY" in str(exc_info.value)


def test_youtube_api_error_handling():
    yt = YouTubeSource(api_key="mock_invalid_key")
    with patch.dict(os.environ, {"YOUTUBE_API_KEY": "mock_invalid_key"}):
        with patch("httpx.Client.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 403
            mock_resp.json.return_value = {
                "error": {
                    "errors": [{"reason": "quotaExceeded"}],
                    "message": "The request cannot be completed because quota exceeded.",
                }
            }
            mock_get.return_value = mock_resp

            # Handles quota error and returns empty without crashing pipeline
            mentions = yt.fetch("Tata STRIVE")
            assert mentions == []


def test_rss_feed_parsing_and_deduplication():
    rss = RSSSource(feeds=["https://example.com/fake_rss"])
    fake_feed = MagicMock()
    fake_feed.bozo = False
    fake_entry_1 = {
        "title": "Tata STRIVE Launches New Skilling Centre - The Hindu",
        "link": "https://thehindu.com/news/national/tata-strive-centre",
        "published": "Tue, 13 Oct 2026 10:00:00 GMT",
        "summary": "Tata STRIVE launches new center for skilling youth in electronics.",
        "source": {"title": "The Hindu"},
    }
    fake_entry_duplicate = {
        "title": "Tata STRIVE Launches New Skilling Centre - The Hindu",
        "link": "https://thehindu.com/news/national/tata-strive-centre",
        "published": "Tue, 13 Oct 2026 10:00:00 GMT",
        "summary": "Duplicate entry with same URL.",
        "source": {"title": "The Hindu"},
    }
    fake_feed.entries = [fake_entry_1, fake_entry_duplicate]

    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"<rss></rss>"
        mock_get.return_value = mock_resp

        with patch("feedparser.parse", return_value=fake_feed):
            mentions = rss.fetch("Tata STRIVE")
            # Should deduplicate by canonical URL
            assert len(mentions) == 1
            m = mentions[0]
            assert "The Hindu" in m.title or "The Hindu" in m.author
            assert m.record_type == "article"
            assert m.source == "rss"


def test_rss_malformed_xml_handling():
    rss = RSSSource(feeds=["https://example.com/broken_feed"])
    fake_feed = MagicMock()
    fake_feed.bozo = True
    fake_feed.bozo_exception = Exception("Malformed XML syntax")
    fake_feed.entries = []

    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"<broken>"
        mock_get.return_value = mock_resp

        with patch("feedparser.parse", return_value=fake_feed):
            # Should not crash application on malformed XML
            mentions = rss.fetch("Tata STRIVE")
            assert mentions == []


def test_hackernews_algolia_parsing():
    hn = HackerNewsSource()
    fake_data = {
        "hits": [
            {
                "objectID": "12345",
                "title": "Ask HN: How is vocational education viewed in tech?",
                "author": "techdev",
                "story_text": "Discussion on practical trade skills and digital apprenticeship.",
                "created_at": "2026-10-12T12:00:00Z",
                "points": 42,
                "num_comments": 18,
            }
        ]
    }
    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = fake_data
        mock_get.return_value = mock_resp

        mentions = hn.fetch("vocational education")
        assert len(mentions) == 1
        assert mentions[0].author == "techdev"
        assert mentions[0].score == 42


def test_bluesky_xrpc_parsing():
    bsky = BlueskySource()
    fake_data = {
        "posts": [
            {
                "uri": "at://did:plc:123/app.bsky.feed.post/456",
                "author": {"handle": "careerguide.bsky.social"},
                "record": {
                    "text": "Great initiative by Tata STRIVE on youth employability skills.",
                    "createdAt": "2026-10-13T08:00:00Z",
                },
                "likeCount": 15,
                "replyCount": 3,
            }
        ]
    }
    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = fake_data
        mock_get.return_value = mock_resp

        mentions = bsky.fetch("Tata STRIVE")
        assert len(mentions) == 1
        assert mentions[0].author == "careerguide.bsky.social"
        assert mentions[0].source == "bluesky"


def test_instagram_failure_states():
    # Instaloader handles errors gracefully
    insta = InstagramSource()
    mentions = insta.fetch("SkillDevelopment")
    assert isinstance(mentions, list)
