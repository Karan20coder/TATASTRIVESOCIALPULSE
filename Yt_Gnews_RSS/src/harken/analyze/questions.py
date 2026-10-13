"""Question and Concern Discovery Engine for Tata STRIVE Social Pulse AI.

Clusters recurring questions, complaints, and information needs from audience
discussions, YouTube comments, and public posts, linking each theme directly
to supporting records.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from harken.models import Mention

QUESTION_CLUSTERS = [
    {
        "key": "eligibility_admission",
        "title": "Course Eligibility & Age Criteria",
        "patterns": [r"who\s+can\s+apply", r"eligib", r"age\s+limit", r"qualification", r"10th\s+pass", r"12th\s+pass", r"graduat"],
        "category": "Admission & Eligibility",
        "default_question": "What are the eligibility requirements and age limits for Tata STRIVE courses?",
    },
    {
        "key": "fees_cost",
        "title": "Course Fees & Free Training Inquiries",
        "patterns": [r"free\s+training", r"free\s+course", r"fees?", r"cost", r"how\s+much\s+fee", r"charges?", r"stipend"],
        "category": "Fees & Financials",
        "default_question": "Is the skill training free, and are stipends provided during the program?",
    },
    {
        "key": "placement_jobs",
        "title": "Placement Guarantee & Job Assistance",
        "patterns": [r"placement\s+guarantee", r"100%\s+placement", r"job\s+milegi", r"salary", r"company\s+placement", r"package"],
        "category": "Placements & Careers",
        "default_question": "What companies hire from Tata STRIVE, and what are typical placement outcomes?",
    },
    {
        "key": "centres_locations",
        "title": "Centre Locations & Online Availability",
        "patterns": [r"where\s+is", r"nearest\s+centre", r"online\s+batch", r"location", r"centre\s+in\s+delhi", r"centre\s+in\s+mumbai", r"hyderabad"],
        "category": "Centre Logistics",
        "default_question": "Where are Tata STRIVE skill development centres located, and are online classes offered?",
    },
    {
        "key": "certificates_validity",
        "title": "Certificate Validity & Government Recognition",
        "patterns": [r"certificate\s+valid", r"nsdc\s+cert", r"government\s+approved", r"recognized", r"certificate\s+delay"],
        "category": "Certification",
        "default_question": "Is the certificate NSDC recognized and valid for private and public sector jobs?",
    },
    {
        "key": "digital_tech_skills",
        "title": "Digital & Tech Course Offerings",
        "patterns": [r"ai\s+course", r"python", r"cyber\s+security", r"digital\s+marketing", r"data\s+analytics", r"coding"],
        "category": "Curriculum",
        "default_question": "What digital and technology skill tracks are offered for IT/fresher career transitions?",
    },
]


@dataclass
class QuestionTheme:
    key: str
    title: str
    category: str
    count: int
    sample_question: str
    supporting_mention_ids: list[str] = field(default_factory=list)
    supporting_urls: list[str] = field(default_factory=list)
    sentiment_breakdown: dict[str, int] = field(default_factory=lambda: {"positive": 0, "neutral": 0, "negative": 0})


class QuestionDiscoverer:
    """Discovers and clusters audience questions from collected records."""

    def discover(self, mentions: list[Mention]) -> list[QuestionTheme]:
        clusters: dict[str, QuestionTheme] = {
            item["key"]: QuestionTheme(
                key=item["key"],
                title=item["title"],
                category=item["category"],
                count=0,
                sample_question=item["default_question"],
                supporting_mention_ids=[],
                supporting_urls=[],
                sentiment_breakdown={"positive": 0, "neutral": 0, "negative": 0},
            )
            for item in QUESTION_CLUSTERS
        }

        # Scan mentions (especially comments, posts, and titles containing '?')
        for m in mentions:
            text = f"{m.title or ''} {m.text or ''}".lower()
            is_question = "?" in text or any(w in text for w in ["how", "what", "where", "can i", "is there", "please help", "sir"])
            # Comments and user posts are high signal for audience needs
            is_social = m.record_type in {"comment", "post"} or m.source in {"youtube", "instagram", "bluesky"}

            for cluster_def in QUESTION_CLUSTERS:
                key = cluster_def["key"]
                patterns = cluster_def["patterns"]
                matched = any(re.search(pat, text) for pat in patterns)
                if matched:
                    c = clusters[key]
                    c.count += 1
                    c.supporting_mention_ids.append(m.id)
                    if m.url and m.url.startswith(("http://", "https://")) and m.url not in c.supporting_urls:
                        c.supporting_urls.append(m.url)
                    s_label = (m.sentiment.value if m.sentiment else "neutral").lower()
                    if s_label in c.sentiment_breakdown:
                        c.sentiment_breakdown[s_label] += 1

                    # If this mention contains an actual question, update sample question
                    if is_question and len(m.text) > 15 and len(m.text) < 160:
                        c.sample_question = m.text.strip()

        # Only return clusters that actually have supporting evidence
        active_themes = [c for c in clusters.values() if c.count > 0]
        active_themes.sort(key=lambda t: t.count, reverse=True)
        return active_themes
