"""Statistical Trend Detection Engine for Tata STRIVE Social Pulse AI.

Calculates deterministic growth velocity, momentum, and volume shifts over
configurable time windows compared against historical baselines.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Literal

from harken.models import Mention

TrendLabel = Literal["emerging", "rising", "stable", "declining", "insufficient_data"]


@dataclass
class TopicTrend:
    topic: str
    label: TrendLabel
    velocity: float  # Percentage change (-100.0 to +∞)
    recent_count: int
    baseline_count: int
    total_records: int
    time_window: str
    calculation_method: str
    source_breakdown: dict[str, int] = field(default_factory=dict)
    sentiment_breakdown: dict[str, int] = field(default_factory=dict)
    supporting_urls: list[str] = field(default_factory=list)
    explanation: str = ""


class TrendEngine:
    """Computes evidence-backed statistical trends from collected records."""

    def __init__(self, window_hours: int = 48, baseline_multiplier: int = 3):
        self.window_hours = window_hours
        self.baseline_hours = window_hours * baseline_multiplier

    def analyze(self, mentions: list[Mention], now: datetime | None = None) -> list[TopicTrend]:
        if not mentions:
            return []

        ref_time = now or datetime.now(timezone.utc)
        recent_cutoff = ref_time - timedelta(hours=self.window_hours)
        baseline_cutoff = ref_time - timedelta(hours=self.baseline_hours)

        # Group mentions by category
        by_category: dict[str, list[Mention]] = defaultdict(list)
        for m in mentions:
            cat = m.category or "Skill Development & Programs"
            by_category[cat].append(m)

        trends: list[TopicTrend] = []

        for category, cat_mentions in by_category.items():
            recent_items = [m for m in cat_mentions if m.created_at >= recent_cutoff]
            baseline_items = [
                m for m in cat_mentions
                if baseline_cutoff <= m.created_at < recent_cutoff
            ]

            recent_count = len(recent_items)
            # Baseline is scaled to the same window duration for fair comparison
            raw_baseline = len(baseline_items)
            scaled_baseline = raw_baseline / 3.0 if raw_baseline > 0 else 0.0

            source_counts: dict[str, int] = defaultdict(int)
            sentiment_counts: dict[str, int] = {"positive": 0, "neutral": 0, "negative": 0}
            sample_urls: list[str] = []

            for m in cat_mentions:
                source_counts[m.source] += 1
                s_lbl = (m.sentiment.value if m.sentiment else "neutral").lower()
                if s_lbl in sentiment_counts:
                    sentiment_counts[s_lbl] += 1
                if m.url and m.url.startswith(("http://", "https://")) and len(sample_urls) < 4:
                    sample_urls.append(m.url)

            # Deterministic label and velocity calculation
            total_cat = len(cat_mentions)
            if total_cat < 3:
                label: TrendLabel = "insufficient_data"
                velocity = 0.0
                explanation = f"Only {total_cat} records collected. Need at least 3 records to compute trend trajectory."
            elif scaled_baseline == 0:
                if recent_count >= 3:
                    label = "emerging"
                    velocity = 100.0
                    explanation = f"Brand new conversation spike ({recent_count} recent items) with no prior baseline activity."
                else:
                    label = "stable"
                    velocity = 0.0
                    explanation = f"Low steady baseline with {recent_count} recent mention(s)."
            else:
                pct_change = ((recent_count - scaled_baseline) / scaled_baseline) * 100.0
                velocity = round(pct_change, 1)

                if velocity >= 50.0 and recent_count >= 3:
                    label = "emerging"
                    explanation = f"Surge of +{velocity}% in recent {self.window_hours}h compared to 7-day average baseline."
                elif velocity >= 15.0:
                    label = "rising"
                    explanation = f"Upward growth of +{velocity}% over the historical baseline."
                elif velocity <= -25.0:
                    label = "declining"
                    explanation = f"Volume softened by {velocity}% compared to previous period."
                else:
                    label = "stable"
                    explanation = f"Volume consistent (velocity {velocity}%) with expected historical rate."

            trends.append(
                TopicTrend(
                    topic=category,
                    label=label,
                    velocity=velocity,
                    recent_count=recent_count,
                    baseline_count=int(scaled_baseline),
                    total_records=total_cat,
                    time_window=f"Recent {self.window_hours}h vs {self.baseline_hours}h baseline",
                    calculation_method="Deterministic window count ratio: ((recent - scaled_baseline) / scaled_baseline) * 100",
                    source_breakdown=dict(source_counts),
                    sentiment_breakdown=sentiment_counts,
                    supporting_urls=sample_urls,
                    explanation=explanation,
                )
            )

        trends.sort(key=lambda t: (t.label == "emerging", t.label == "rising", t.recent_count), reverse=True)
        return trends
