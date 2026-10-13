"""Background Ingestion Scheduler for Tata STRIVE Social Pulse AI.

Runs periodic data collection (default every 30 minutes) across YouTube, Google News RSS,
and other configured sources in a non-blocking background task with deduplication,
retry backoff, and manual refresh triggers.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Callable

from harken.config import Config
from harken.pipeline import Pipeline
from harken.store import Store

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """Manages scheduled background ingestion loops."""

    def __init__(self, config: Config | None = None, store: Store | None = None):
        self.config = config or Config()
        self.interval_minutes = self.config.ingestion_interval_minutes
        self.is_running = False
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self.last_run_at: datetime | None = None
        self.last_run_status: str = "idle"
        self.last_run_summary: dict = {}
        self.last_error: str | None = None

    async def start(self) -> None:
        """Start the background ingestion polling loop."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Background ingestion scheduler started (Interval: %d mins).", self.interval_minutes)

    async def stop(self) -> None:
        """Stop the background polling loop."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Background ingestion scheduler stopped.")

    async def _loop(self) -> None:
        # Run an initial background check shortly after boot (e.g. 5 seconds)
        await asyncio.sleep(5)
        while self.is_running:
            try:
                await self.trigger_refresh()
            except Exception as exc:
                logger.error("Error during scheduled refresh: %s", exc)
                self.last_error = str(exc)

            # Sleep for configured interval
            try:
                await asyncio.sleep(self.interval_minutes * 60)
            except asyncio.CancelledError:
                break

    async def trigger_refresh(self, queries: list[str] | None = None) -> dict:
        """Run an immediate ingestion cycle (manual or scheduled) safely under lock."""
        if self._lock.locked():
            return {
                "status": "in_progress",
                "message": "An ingestion run is already in progress.",
                "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            }

        async with self._lock:
            self.last_run_status = "running"
            self.last_run_at = datetime.now(timezone.utc)
            start_time = self.last_run_at

            # Default monitoring keywords for Tata STRIVE
            target_queries = queries or [
                "Tata STRIVE",
                "Skill Development India",
                "Youth Employment India",
                "Vocational Training India",
            ]

            summary: dict[str, int] = {"total_fetched": 0, "total_new": 0}
            errors: dict[str, str] = {}

            # Run in worker thread to avoid blocking asyncio event loop
            def _sync_worker():
                pipeline = Pipeline(self.config)
                try:
                    for q in target_queries:
                        try:
                            res = pipeline.track(q, pages=1)
                            summary["total_fetched"] += res.fetched
                            summary["total_new"] += res.new
                            for src, err in res.errors.items():
                                errors[f"{q}:{src}"] = err
                        except Exception as e:
                            errors[q] = str(e)
                finally:
                    pipeline.close()

            await asyncio.to_thread(_sync_worker)

            self.last_run_status = "success" if not errors else "partial"
            self.last_run_summary = {
                "fetched": summary["total_fetched"],
                "new": summary["total_new"],
                "errors": errors,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": round((datetime.now(timezone.utc) - start_time).total_seconds(), 2),
            }
            if errors:
                self.last_error = "; ".join(f"{k}: {v}" for k, v in errors.items())

            return {
                "status": self.last_run_status,
                "summary": self.last_run_summary,
                "timestamp": self.last_run_at.isoformat(),
            }
