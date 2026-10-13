"""Experimental Instagram connector for Tata STRIVE Social Pulse AI using Instaloader.

Allows collection from explicitly specified public profiles or hashtags when access is available.
Handles login challenges, checkpoints, and rate limits gracefully without breaking other connectors.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from harken.models import Mention
from harken.sources.base import FetchPage, Source, strip_html

logger = logging.getLogger(__name__)


class InstagramSource(Source):
    name = "instagram"
    label = "Instagram (Experimental)"
    needs_config = False

    def __init__(
        self,
        session_file: str | None = None,
        username: str | None = None,
        **options,
    ):
        super().__init__(**options)
        self.session_file = session_file or os.getenv("INSTAGRAM_SESSION_FILE")
        self.username = username or os.getenv("INSTAGRAM_USERNAME")

    def fetch(self, query: str, limit: int = 15) -> list[Mention]:
        return self.fetch_page(query, limit=limit).mentions

    def fetch_page(
        self,
        query: str,
        limit: int = 15,
        *,
        cursor: str | None = None,
        since: datetime | None = None,
    ) -> FetchPage:
        # Instaloader is user-initiated and optional
        mentions: list[Mention] = []
        try:
            import instaloader
        except ImportError:
            logger.info("instaloader package is not installed; Instagram connector inactive.")
            return FetchPage([], None)

        loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            max_connection_attempts=1,
            request_timeout=10.0,
        )

        # Optional session loading
        if self.username:
            try:
                loader.load_session_from_file(self.username, filename=self.session_file)
            except Exception as exc:
                logger.debug("Instagram session file not loaded for user %s: %s", self.username, exc)

        clean_tag = query.replace(" ", "").replace("#", "").strip()
        if not clean_tag:
            clean_tag = "SkillDevelopment"

        try:
            # Query hashtag posts
            hashtag = instaloader.Hashtag.from_name(loader.context, clean_tag)
            count = 0
            for post in hashtag.get_posts():
                if count >= min(limit, 10):
                    break

                caption = strip_html(post.caption or "")
                post_url = f"https://www.instagram.com/p/{post.shortcode}/"
                post_date = post.date_utc.replace(tzinfo=timezone.utc) if post.date_utc else datetime.now(timezone.utc)

                if since and post_date <= since:
                    continue

                mentions.append(
                    Mention(
                        source=self.name,
                        query=query,
                        author=post.owner_username or "instagram_user",
                        title=f"Instagram #{clean_tag} post by @{post.owner_username}" if post.owner_username else f"#{clean_tag} post",
                        text=caption,
                        url=post_url,
                        created_at=post_date,
                        score=post.likes,
                        record_type="post",
                        likes=post.likes,
                        comments_count=post.comments,
                        confidence=0.80,
                    )
                )
                count += 1
        except Exception as exc:
            # Rate limit, login challenge, or network restriction: log and gracefully return empty without failing run
            logger.warning("Instagram collection for query %r halted gracefully: %s", query, exc)

        return FetchPage(mentions[:limit], None)
