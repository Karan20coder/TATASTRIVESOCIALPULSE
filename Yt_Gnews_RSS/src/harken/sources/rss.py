"""Google News RSS / Atom source for Tata STRIVE Social Pulse AI.

Monitors news coverage across brand, skill development, youth employment,
vocational training, and government skilling initiatives without requiring an API key.
"""

from __future__ import annotations

import os
import re
from calendar import timegm
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import feedparser
import httpx

from harken.models import Mention
from harken.sources.base import FetchPage, Source, strip_html

DEFAULT_FEEDS = [
    "https://news.google.com/rss/search?q=%22Tata+STRIVE%22&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=skill+development+India&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=youth+employment+India&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=vocational+training+India&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=%22Ministry+of+Skill+Development%22&hl=en-IN&gl=IN&ceid=IN:en",
]


class RSSSource(Source):
    name = "rss"
    label = "News / RSS"
    needs_config = False

    def __init__(self, feeds: list[str] | None = None, **options):
        super().__init__(**options)
        self._is_default = feeds is None and not options.get("feeds")
        configured_feeds = feeds if feeds is not None else options.get("feeds")
        self.feeds = list(configured_feeds) if configured_feeds is not None else []

    def fetch(self, query: str, limit: int = 50) -> list[Mention]:
        return self.fetch_page(query, limit=limit).mentions

    def fetch_page(
        self,
        query: str,
        limit: int = 50,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> FetchPage:
        if not self.feeds:
            raise RuntimeError("HARKEN_RSS_FEEDS requires at least one feed URL")

        q = query.casefold().strip()
        mentions: list[Mention] = []
        seen_urls: set[str] = set()

        feeds_to_poll = list(self.feeds)

        # Only inject custom Google News RSS search URL if we are in default Google News mode
        if self._is_default and q and q not in {"tata strive", "skill development", "youth employment", "vocational training"}:
            custom_feed = (
                f"https://news.google.com/rss/search?q={httpx.URL('', params={'q': query}).params['q']}"
                f"&hl=en-IN&gl=IN&ceid=IN:en"
            )
            if custom_feed not in feeds_to_poll:
                feeds_to_poll.insert(0, custom_feed)

        with self._client(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as client:
            for feed_url in feeds_to_poll:
                try:
                    resp = client.get(feed_url, timeout=15.0)
                    resp.raise_for_status()
                except httpx.HTTPError:
                    continue  # Graceful fault tolerance: one failed feed does not break others

                parsed = feedparser.parse(resp.content)
                for entry in parsed.entries:
                    raw_title = entry.get("title", "")
                    link = entry.get("link")
                    if not link or link in seen_urls:
                        continue

                    author_name = entry.get("author")
                    source_elem = entry.get("source")
                    source_name = None
                    if isinstance(source_elem, dict):
                        source_name = source_elem.get("title")
                    elif hasattr(source_elem, "title"):
                        source_name = source_elem.title

                    clean_title = raw_title
                    if not source_name and " - " in raw_title:
                        parts = raw_title.rsplit(" - ", 1)
                        clean_title = parts[0].strip()
                        source_name = parts[1].strip()
                    elif source_name and raw_title.endswith(f" - {source_name}"):
                        clean_title = raw_title[: -len(f" - {source_name}")].strip()

                    final_author = author_name or source_name or "News Publisher"
                    summary = strip_html(entry.get("summary", ""))
                    blob = f"{clean_title} {summary}".casefold()

                    is_direct_feed = query.lower() in feed_url.lower() or "tata+strive" in feed_url.lower()
                    if not is_direct_feed and q and q not in blob:
                        skilling_terms = {"skill", "employ", "job", "vocational", "training", "career", "tata"}
                        if not any(term in blob for term in skilling_terms):
                            continue

                    created = _entry_time(entry)
                    if since and created <= since:
                        continue

                    seen_urls.add(link)
                    mentions.append(
                        Mention(
                            source=self.name,
                            query=query,
                            author=final_author,
                            title=clean_title or None,
                            text=summary,
                            url=link,
                            created_at=created,
                            record_type="article",
                            origin_feed=feed_url,
                            confidence=0.92,
                        )
                    )

        return FetchPage(mentions[:limit], None)


def _entry_time(entry) -> datetime:
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime.fromtimestamp(timegm(t), tz=timezone.utc)
    return datetime.now(timezone.utc)
