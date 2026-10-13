"""GNews API connector for Tata STRIVE Social Pulse AI.

Queries gnews.io API for mainstream Indian and global news coverage on
skilling, employability, and Tata STRIVE brand mentions.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import httpx
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

from harken.models import Mention
from harken.sources.base import FetchPage, Source, strip_html

logger = logging.getLogger(__name__)

_API = "https://gnews.io/api/v4/search"


class GNewsSource(Source):
    name = "gnews"
    label = "GNews API"
    needs_config = True

    def __init__(self, api_key: str | None = None, **options):
        super().__init__(**options)
        self.api_key = api_key or os.getenv("GNEWS_API_KEY") or os.getenv("HARKEN_GNEWS_API_KEY")

    def fetch(self, query: str, limit: int = 25) -> list[Mention]:
        return self.fetch_page(query, limit=limit).mentions

    def fetch_page(
        self,
        query: str,
        limit: int = 25,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> FetchPage:
        if not self.api_key:
            raise RuntimeError("GNews requires GNEWS_API_KEY")

        params = {
            "q": query,
            "apikey": self.api_key,
            "lang": "en",
            "country": "in",
            "max": min(limit, 10),
        }
        if since:
            params["from"] = since.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

        mentions: list[Mention] = []
        with self._client() as client:
            try:
                resp = client.get(_API, params=params, timeout=12.0)
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPError as exc:
                logger.warning("GNews API request failed: %s", exc)
                return FetchPage([], None)

        for article in data.get("articles", []):
            url = article.get("url")
            if not url:
                continue

            source_info = article.get("source") or {}
            source_name = source_info.get("name") or "News"
            title = strip_html(article.get("title", ""))
            desc = strip_html(article.get("description", ""))
            published = _parse_datetime(article.get("publishedAt"))

            mentions.append(
                Mention(
                    source=self.name,
                    query=query,
                    author=source_name,
                    title=title or None,
                    text=desc,
                    url=url,
                    created_at=published,
                    record_type="article",
                    origin_feed="gnews.io",
                    confidence=0.94,
                )
            )

        return FetchPage(mentions[:limit], None)


def _parse_datetime(val: str | None) -> datetime:
    if val:
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)
