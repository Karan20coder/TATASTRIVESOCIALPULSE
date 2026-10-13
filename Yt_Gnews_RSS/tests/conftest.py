"""Test fixtures and environment isolation."""

import os
import pytest


@pytest.fixture(autouse=True)
def clean_env_defaults(monkeypatch):
    """Ensure local .env development variables do not leak into unit tests that assert on default configurations."""
    for var in [
        "HARKEN_DB",
        "HARKEN_SOURCES",
        "YOUTUBE_API_KEY",
        "HARKEN_YOUTUBE_API_KEY",
        "GNEWS_API_KEY",
        "HARKEN_GNEWS_API_KEY",
    ]:
        if var in os.environ:
            monkeypatch.delenv(var, raising=False)
