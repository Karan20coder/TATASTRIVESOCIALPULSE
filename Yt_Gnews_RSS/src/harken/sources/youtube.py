"""YouTube Data API v3 live connector for Tata STRIVE Social Pulse AI.

Retrieves video metadata, view/like statistics, and public comment threads
with graceful quota management and error handling.
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

_SEARCH_API = "https://www.googleapis.com/youtube/v3/search"
_VIDEOS_API = "https://www.googleapis.com/youtube/v3/videos"
_COMMENTS_API = "https://www.googleapis.com/youtube/v3/commentThreads"


class YouTubeSource(Source):
    name = "youtube"
    label = "YouTube"
    needs_config = True

    def __init__(self, api_key: str | None = None, **options):
        super().__init__(**options)
        self.api_key = api_key

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
        if not self.api_key:
            raise RuntimeError("HARKEN_YOUTUBE_API_KEY: YouTube connector requires YOUTUBE_API_KEY or HARKEN_YOUTUBE_API_KEY")

        search_params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "order": "date",
            "maxResults": min(limit, 25),
        }
        if cursor:
            search_params["pageToken"] = cursor
        if since:
            search_params["publishedAfter"] = _rfc3339(since)

        mentions: list[Mention] = []
        next_page_token = None

        with self._client(headers={"X-Goog-Api-Key": self.api_key}) as client:
            try:
                resp = client.get(_SEARCH_API, params=search_params)
                resp.raise_for_status()
                search_data = resp.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 403:
                    logger.warning("YouTube API quota exceeded or access restricted: %s", exc)
                raise
            except httpx.HTTPError:
                raise

            items = search_data.get("items", [])
            next_page_token = search_data.get("nextPageToken")
            video_ids = [
                item["id"]["videoId"]
                for item in items
                if item.get("id", {}).get("videoId")
            ]

            # Batch fetch video statistics (views, likes, comments count)
            stats_by_id: dict[str, dict] = {}
            if video_ids:
                try:
                    video_resp = client.get(
                        _VIDEOS_API,
                        params={
                            "part": "snippet,statistics",
                            "id": ",".join(video_ids[:50]),
                        },
                    )
                    if video_resp.is_success:
                        for v in video_resp.json().get("items", []):
                            stats_by_id[v["id"]] = v
                except Exception as exc:
                    logger.warning("Failed to fetch detailed video statistics: %s", exc)

            # Ingest video records
            videos_for_comments: list[tuple[str, str]] = []
            for item in items:
                video_id = (item.get("id") or {}).get("videoId")
                if not video_id:
                    continue

                snippet = item.get("snippet") or {}
                detailed = stats_by_id.get(video_id, {})
                stats = detailed.get("statistics") or {}
                if detailed.get("snippet"):
                    snippet = detailed["snippet"]

                views = _safe_int(stats.get("viewCount"))
                likes = _safe_int(stats.get("likeCount"))
                comment_count = _safe_int(stats.get("commentCount"))
                title = strip_html(snippet.get("title", ""))
                channel = strip_html(snippet.get("channelTitle", ""))

                video_mention = Mention(
                    source=self.name,
                    query=query,
                    author=channel or None,
                    title=title or None,
                    text=strip_html(snippet.get("description", "")),
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    created_at=_parse_datetime(snippet.get("publishedAt")),
                    score=likes or 0,
                    record_type="video",
                    views=views,
                    likes=likes,
                    comments_count=comment_count,
                    confidence=0.95,
                )
                mentions.append(video_mention)

                if comment_count and comment_count > 0 and len(videos_for_comments) < 4:
                    videos_for_comments.append((video_id, title))

            # Fetch public comments for top videos to understand audience feedback
            for vid, vtitle in videos_for_comments:
                try:
                    c_resp = client.get(
                        _COMMENTS_API,
                        params={
                            "part": "snippet",
                            "videoId": vid,
                            "maxResults": 6,
                            "order": "relevance",
                            "textFormat": "plainText",
                        },
                    )
                    if c_resp.is_success:
                        c_data = c_resp.json()
                        for c_item in c_data.get("items", []):
                            top_comment = (
                                (c_item.get("snippet") or {}).get("topLevelComment") or {}
                            )
                            c_snippet = top_comment.get("snippet") or {}
                            c_id = top_comment.get("id") or c_item.get("id")
                            c_author = c_snippet.get("authorDisplayName")
                            c_text = strip_html(c_snippet.get("textDisplay", ""))
                            c_likes = _safe_int(c_snippet.get("likeCount"))
                            c_published = _parse_datetime(c_snippet.get("publishedAt"))

                            if c_text:
                                mentions.append(
                                    Mention(
                                        source=self.name,
                                        query=query,
                                        author=c_author or "YouTube User",
                                        title=f"Comment on: {vtitle[:70]}",
                                        text=c_text,
                                        url=f"https://www.youtube.com/watch?v={vid}&lc={c_id}"
                                        if c_id
                                        else f"https://www.youtube.com/watch?v={vid}",
                                        created_at=c_published,
                                        score=c_likes or 0,
                                        record_type="comment",
                                        likes=c_likes,
                                        confidence=0.88,
                                    )
                                )
                except Exception as exc:
                    # Non-fatal: comments disabled or network hiccup on specific video
                    logger.debug("Comments skipped for video %s: %s", vid, exc)

        return FetchPage(mentions[:limit], next_page_token)


def _safe_int(val: str | int | None) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _parse_datetime(value: str | None) -> datetime:
    if value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _rfc3339(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
