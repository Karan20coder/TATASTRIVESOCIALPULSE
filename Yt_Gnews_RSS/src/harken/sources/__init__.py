"""Pluggable mention sources for Tata STRIVE Social Pulse AI.

Each source implements Source. New sources are registered in REGISTRY.
"""

from __future__ import annotations

from harken.sources.base import Source
from harken.sources.bluesky import BlueskySource
from harken.sources.gnews import GNewsSource
from harken.sources.hackernews import HackerNewsSource
from harken.sources.instagram import InstagramSource
from harken.sources.mastodon import MastodonSource
from harken.sources.reddit import RedditSource
from harken.sources.rss import RSSSource
from harken.sources.stackoverflow import StackOverflowSource
from harken.sources.x import XSource
from harken.sources.youtube import YouTubeSource

REGISTRY: dict[str, type[Source]] = {
    YouTubeSource.name: YouTubeSource,
    RSSSource.name: RSSSource,
    GNewsSource.name: GNewsSource,
    HackerNewsSource.name: HackerNewsSource,
    BlueskySource.name: BlueskySource,
    InstagramSource.name: InstagramSource,
    RedditSource.name: RedditSource,
    MastodonSource.name: MastodonSource,
    StackOverflowSource.name: StackOverflowSource,
    XSource.name: XSource,
}

# Default sources prioritized for Tata STRIVE
DEFAULT_SOURCES = ["youtube", "rss", "gnews", "hackernews"]

__all__ = ["Source", "REGISTRY", "DEFAULT_SOURCES"]
