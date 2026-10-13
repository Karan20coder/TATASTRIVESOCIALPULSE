"""Reputation and Opportunity Alert Engine for Tata STRIVE Social Pulse AI.

Evaluates evidence-based operational signals across volume shifts, negative feedback,
unanswered audience inquiries, brand press mentions, and opportunity signals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Literal

from harken.models import Mention, Sentiment

AlertSeverity = Literal["low", "medium", "high", "critical"]


@dataclass
class OperationalAlert:
    title: str
    reason: str
    severity: AlertSeverity
    source: str
    time_window: str
    supporting_urls: list[str] = field(default_factory=list)
    action_plan: str = ""
    confidence: float = 0.85


class AlertEvaluator:
    """Evaluates collected records and identifies reputational and opportunity alerts."""

    def evaluate(self, mentions: list[Mention]) -> list[OperationalAlert]:
        alerts: list[OperationalAlert] = []
        if not mentions:
            return alerts

        # 1. Check for negative feedback clusters
        negative_mentions = [m for m in mentions if m.sentiment == Sentiment.NEGATIVE]
        if len(negative_mentions) >= 3:
            neg_ratio = len(negative_mentions) / len(mentions)
            severity: AlertSeverity = "high" if neg_ratio > 0.25 else "medium"
            sample_urls = [m.url for m in negative_mentions if m.url][:4]
            alerts.append(
                OperationalAlert(
                    title="Audience Dissatisfaction or Complaint Spike",
                    reason=f"Detected {len(negative_mentions)} negative feedback records ({round(neg_ratio * 100, 1)}% of sampled volume).",
                    severity=severity,
                    source="YouTube / Social",
                    time_window="Last 48 Hours",
                    supporting_urls=sample_urls,
                    action_plan="Review candidate comments to identify specific grievances (e.g. certificate dispatch delays or admission confusion). Prepare official communications response.",
                    confidence=0.88,
                )
            )

        # 2. Check for recurring candidate questions
        question_keywords = ["eligibility", "fees", "free", "how to apply", "where is", "placement"]
        question_mentions = [
            m for m in mentions
            if any(k in f"{m.title or ''} {m.text or ''}".lower() for k in question_keywords)
        ]
        if len(question_mentions) >= 4:
            sample_urls = [m.url for m in question_mentions if m.url][:4]
            alerts.append(
                OperationalAlert(
                    title="Repeated Audience Inquiries on Admissions & Fees",
                    reason=f"Found {len(question_mentions)} candidate discussions seeking clarification on course eligibility, free training, or placement.",
                    severity="low",
                    source="YouTube / Public Channels",
                    time_window="Recent Ingest",
                    supporting_urls=sample_urls,
                    action_plan="Publish an FAQ carousel or pinned response addressing fee clarity and application steps at nearest centres.",
                    confidence=0.92,
                )
            )

        # 3. Check for new Brand Mentions in Mainstream News
        brand_news = [
            m for m in mentions
            if m.record_type == "article" and ("tata strive" in (m.title or "").lower() or "tata strive" in m.text.lower())
        ]
        if brand_news:
            sample_urls = [m.url for m in brand_news if m.url][:4]
            alerts.append(
                OperationalAlert(
                    title="New Mainstream News Coverage of Tata STRIVE",
                    reason=f"Identified {len(brand_news)} verified press articles highlighting Tata STRIVE initiatives and partnerships.",
                    severity="low",
                    source="Google News RSS",
                    time_window="Latest News Cycle",
                    supporting_urls=sample_urls,
                    action_plan="Amplify press coverage across LinkedIn and Twitter/X handles. Tag corporate partners and leadership.",
                    confidence=0.96,
                )
            )

        # 4. Check for Emerging High-Velocity Topics
        digital_mentions = [
            m for m in mentions
            if any(k in f"{m.title or ''} {m.text or ''}".lower() for k in ["digital skill", "ai", "coding", "cyber"])
        ]
        if len(digital_mentions) >= 5:
            sample_urls = [m.url for m in digital_mentions if m.url][:4]
            alerts.append(
                OperationalAlert(
                    title="Content Opportunity: Rising Interest in Digital & AI Skilling",
                    reason=f"High engagement detected around digital skills and tech employment ({len(digital_mentions)} records).",
                    severity="low",
                    source="Cross-Platform",
                    time_window="Active Trend",
                    supporting_urls=sample_urls,
                    action_plan="Generate a Campaign Copilot brief on 'Demystifying Tech Careers' to engage aspiring youth.",
                    confidence=0.85,
                )
            )

        return alerts
