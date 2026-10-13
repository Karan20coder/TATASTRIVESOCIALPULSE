"""AI News Topic Intelligence & Prioritisation Engine for Tata STRIVE Social Pulse AI.

Analyzes collected news articles from Google News RSS and GNews API,
cautiously deduplicates syndicated and multi-query copies, classifies articles
into distinct primary categories, computes transparent priority rankings for
Tata STRIVE's communications team, and generates evidence-backed strategic recommendations.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from harken.models import Mention

# -----------------------------------------------------------------------------
# Configurable Topic Taxonomy & Strategic Relevance Weights
# -----------------------------------------------------------------------------

@dataclass
class TopicDefinition:
    key: str
    name: str
    description: str
    color: str
    keywords: list[str]
    relevance_weight: float  # Strategic relevance to Tata STRIVE's skilling & youth employability mission (0.0 - 1.0)
    priority_rationale: str


DEFAULT_TOPICS: list[TopicDefinition] = [
    TopicDefinition(
        key="tata_strive",
        name="Tata STRIVE Brand Mentions",
        description="Direct institutional coverage of Tata STRIVE, TCIT initiatives, partnerships, and skill centre achievements.",
        color="#0ea5e9",  # Tata Azure Cyan
        keywords=[
            "tata strive",
            "tatastrive",
            "tcit",
            "tata trusts skilling",
            "tssdc",
            "tata community initiatives trust",
            "tata skill development",
        ],
        relevance_weight=1.00,
        priority_rationale="Core brand visibility and programmatic milestone coverage directly tied to Tata STRIVE leadership.",
    ),
    TopicDefinition(
        key="skill_development",
        name="Skill Development & Vocational Training",
        description="Vocational education, ITI modernisation, craft training, apprenticeship models, and technician upskilling.",
        color="#10b981",  # Emerald
        keywords=[
            "skill development",
            "vocational training",
            "vocational education",
            "iti",
            "polytechnic",
            "apprentice",
            "apprenticeship",
            "skilling centre",
            "vocational",
            "technician training",
            "hands-on skills",
        ],
        relevance_weight=0.95,
        priority_rationale="Core operational focus of Tata STRIVE's classroom and workshop skilling ecosystems.",
    ),
    TopicDefinition(
        key="youth_employment",
        name="Youth Employment & Employability",
        description="Job fairs, placement outcomes, wages, unemployment metrics, entry-level hiring trends, and career mobility.",
        color="#3b82f6",  # Royal Blue
        keywords=[
            "youth employment",
            "employability",
            "placement",
            "job fair",
            "rozgar mela",
            "campus hiring",
            "entry level jobs",
            "job creation",
            "unemployment rate",
            "workforce participation",
            "job placement",
        ],
        relevance_weight=0.92,
        priority_rationale="Direct measure of Tata STRIVE's ultimate impact: gainful and dignified livelihood placement.",
    ),
    TopicDefinition(
        key="digital_skills",
        name="Digital Skills & Technology Careers",
        description="AI readiness, cloud computing, cybersecurity, software coding, data skills, and tech sector demand.",
        color="#8b5cf6",  # Violet
        keywords=[
            "digital skills",
            "artificial intelligence",
            "ai skilling",
            "cybersecurity",
            "cloud computing",
            "data analytics",
            "software skills",
            "it-ites",
            "digital literacy",
            "genai",
            "coding",
            "tech jobs",
        ],
        relevance_weight=0.88,
        priority_rationale="High-growth career tracks critical for preparing underprivileged youth for industry 4.0 wages.",
    ),
    TopicDefinition(
        key="career_readiness",
        name="Career Readiness & Freshers",
        description="Soft skills, communication training, workplace etiquette, resume building, and life skills (YDM).",
        color="#f59e0b",  # Amber
        keywords=[
            "career readiness",
            "freshers",
            "soft skills",
            "life skills",
            "workplace readiness",
            "interview preparation",
            "communication skills",
            "first time job seekers",
            "career guidance",
            "youth development",
        ],
        relevance_weight=0.85,
        priority_rationale="Aligns with Tata STRIVE's proprietary Youth Development Module (YDM) differentiator.",
    ),
    TopicDefinition(
        key="education_training",
        name="Education & Training Programmes",
        description="Higher education reforms, university-industry linkages, NEP 2020 vocationalisation, and certificates.",
        color="#06b6d4",  # Cyan Teal
        keywords=[
            "education",
            "nep 2020",
            "curriculum",
            "university",
            "college",
            "diploma",
            "certification",
            "training programme",
            "capacity building",
            "academic",
            "school education",
        ],
        relevance_weight=0.75,
        priority_rationale="Broader educational landscape influencing pipelines into specialised skilling centres.",
    ),
    TopicDefinition(
        key="government_initiatives",
        name="Government Skilling Initiatives",
        description="PMKVY, Skill India Mission, NSDC, MSDE policy announcements, state skill development missions, and subsidies.",
        color="#ec4899",  # Pink
        keywords=[
            "ministry of skill development",
            "msde",
            "nsdc",
            "skill india",
            "pmkvy",
            "pradhan mantri kaushal",
            "government scheme",
            "naps",
            "sector skill council",
            "state skill development",
            "dgt",
        ],
        relevance_weight=0.82,
        priority_rationale="Policy shifts and public scheme opportunities for institutional collaboration.",
    ),
    TopicDefinition(
        key="other_industry",
        name="Other Skilling & Industry News",
        description="General industry hiring trends, corporate CSR, economic updates, and cross-sector vocational developments.",
        color="#64748b",  # Slate
        keywords=[],  # Fallback category
        relevance_weight=0.50,
        priority_rationale="Macro-economic context and general industry movements.",
    ),
]


# -----------------------------------------------------------------------------
# Output Data Structures
# -----------------------------------------------------------------------------

@dataclass
class DeduplicationStats:
    total_raw_articles: int
    total_unique_articles: int
    duplicates_removed: int
    unique_publishers_count: int
    deduplication_method: str = "Canonical URL normalization + Alphanumeric Headline Fingerprinting"
    limitations_note: str = (
        "Articles syndicated across distinct wire services with altered headlines or URLs without tracking tags "
        "may be counted as separate publications. Deduplication is conservative to preserve unique regional coverage."
    )


@dataclass
class TopicArticleView:
    id: str
    title: str
    author: str
    source: str
    url: str
    published_date: str
    published_iso: str
    snippet: str
    query: str
    is_primary: bool = True


@dataclass
class TopicMetric:
    key: str
    name: str
    color: str
    description: str
    article_count: int
    percentage_share: float
    relevance_weight: float
    relevance_score_pct: int
    priority_score: int
    momentum_label: str  # "Accelerating", "Consistent", "Emerging", "Baseline"
    momentum_badge: str  # css class
    publisher_count: int
    publishers: list[str]
    latest_date: str
    supporting_articles: list[TopicArticleView]
    explanation: str


@dataclass
class AIRecommendation:
    topic: str
    priority_score: int
    communication_objective: str
    campaign_idea: str
    content_concept: str
    target_audience: str
    suggested_hashtags: list[str]
    evidence_headline: str
    evidence_publisher: str
    evidence_url: str


@dataclass
class TopicTimeSeriesPoint:
    date: str
    topic_counts: dict[str, int]
    total_articles: int


@dataclass
class TopicIntelligencePayload:
    generated_at: str
    filters_applied: dict[str, Any]
    deduplication: DeduplicationStats
    summary_cards: dict[str, Any]
    segments: list[dict[str, Any]]
    priority_topics: list[dict[str, Any]]
    time_series: list[dict[str, Any]]
    all_topic_names: list[str]
    recommendations: list[dict[str, Any]]
    scoring_methodology: dict[str, Any]
    articles_by_topic: dict[str, list[dict[str, Any]]]


# -----------------------------------------------------------------------------
# Core Engine
# -----------------------------------------------------------------------------

class TopicIntelligenceEngine:
    """Production-grade topic intelligence engine for Tata STRIVE news analytics."""

    def __init__(self, topics: list[TopicDefinition] | None = None):
        self.topics = topics or DEFAULT_TOPICS
        self._fallback_topic = next((t for t in self.topics if t.key == "other_industry"), self.topics[-1])
        self._cache: dict[str, Tuple[str, TopicIntelligencePayload]] = {}

    @staticmethod
    def normalize_url(url: str | None) -> str:
        """Strip tracking query params (utm_*, ref, etc.) and protocol differences to obtain canonical URL."""
        if not url:
            return ""
        try:
            parsed = urlparse(url.strip())
            # Strip common marketing/tracking query parameters
            query_params = parse_qs(parsed.query, keep_blank_values=False)
            filtered_params = {
                k: v for k, v in query_params.items()
                if not (k.startswith("utm_") or k in {"ref", "source", "oc", "ved", "usg", "fbclid", "gclid"})
            }
            clean_query = urlencode(filtered_params, doseq=True)
            clean_path = parsed.path.rstrip("/")
            # Standardize scheme and netloc to lowercase
            return urlunparse((
                "https",
                parsed.netloc.lower(),
                clean_path,
                "",
                clean_query,
                "",
            ))
        except Exception:
            return url.strip().lower()

    @staticmethod
    def fingerprint_headline(title: str | None) -> str:
        """Create a resilient alphanumeric slug for headline deduplication."""
        if not title:
            return ""
        # Remove trailing publisher signatures (e.g. " - Times of India", " | Mint")
        t = re.sub(r"\s+[-–—|]\s+[A-Za-z0-9\s.&]+$", "", title)
        # Keep only lowercase letters and digits
        slug = re.sub(r"[^a-z0-9]", "", t.casefold())
        return slug[:120]

    def deduplicate_articles(self, mentions: list[Mention]) -> Tuple[list[Mention], DeduplicationStats]:
        """Cautiously deduplicate articles by canonical URL and headline fingerprint."""
        raw_count = len(mentions)
        unique_mentions: list[Mention] = []
        seen_urls: set[str] = set()
        seen_slugs: set[str] = set()
        unique_publishers: set[str] = set()

        for m in mentions:
            # We only analyze news articles
            if m.record_type != "article" and m.source not in {"rss", "gnews"}:
                continue

            can_url = self.normalize_url(m.url)
            slug = self.fingerprint_headline(m.title)

            # Check duplicate conditions
            is_url_dup = bool(can_url and can_url in seen_urls)
            is_slug_dup = bool(slug and len(slug) >= 15 and slug in seen_slugs)

            if is_url_dup or is_slug_dup:
                continue

            if can_url:
                seen_urls.add(can_url)
            if slug and len(slug) >= 15:
                seen_slugs.add(slug)

            if m.author:
                unique_publishers.add(m.author.strip())

            unique_mentions.append(m)

        # Sort chronologically (newest first)
        unique_mentions.sort(key=lambda m: m.created_at, reverse=True)

        stats = DeduplicationStats(
            total_raw_articles=raw_count,
            total_unique_articles=len(unique_mentions),
            duplicates_removed=raw_count - len(unique_mentions),
            unique_publishers_count=len(unique_publishers),
        )
        return unique_mentions, stats

    def categorize_article(self, article: Mention) -> TopicDefinition:
        """Assign an article to exactly one primary category (highest weighted score, no double counting)."""
        text_corpus = f"{article.title or ''} {article.text or ''}".casefold()
        
        # Priority check for direct Tata STRIVE brand mentions
        tata_strive_def = next((t for t in self.topics if t.key == "tata_strive"), None)
        if tata_strive_def and any(kw in text_corpus for kw in tata_strive_def.keywords):
            return tata_strive_def

        best_topic: Optional[TopicDefinition] = None
        best_score = 0.0

        for topic in self.topics:
            if topic.key == "other_industry" or topic.key == "tata_strive":
                continue
            
            # Count keyword hits with weighted matches
            hits = 0
            for kw in topic.keywords:
                if kw in text_corpus:
                    # Give higher weight to matches appearing in the headline
                    if article.title and kw in article.title.casefold():
                        hits += 3
                    else:
                        hits += 1

            if hits > 0:
                weighted_score = hits * topic.relevance_weight
                if weighted_score > best_score:
                    best_score = weighted_score
                    best_topic = topic

        return best_topic if best_topic else self._fallback_topic

    @staticmethod
    def calculate_percentages(counts: dict[str, int], total: int) -> dict[str, float]:
        """Compute exact percentages ensuring their sum equals 100.0% accounting for rounding."""
        if total <= 0 or not counts:
            return {k: 0.0 for k in counts}

        # Largest Remainder Method
        exact = {k: (c / total) * 100.0 for k, c in counts.items()}
        floored = {k: math.floor(v * 10) / 10 for k, v in exact.items()}
        remainder = {k: exact[k] - floored[k] for k in counts}

        # Calculate difference from 100.0
        diff = round(100.0 - sum(floored.values()), 1)
        # Distribute 0.1 to the items with highest remainders
        sorted_keys = sorted(counts.keys(), key=lambda k: remainder[k], reverse=True)
        steps = int(round(diff * 10))
        for i in range(min(steps, len(sorted_keys))):
            floored[sorted_keys[i]] = round(floored[sorted_keys[i]] + 0.1, 1)

        return floored

    def calculate_priority_score(
        self,
        topic: TopicDefinition,
        articles: list[Mention],
        total_unique_articles: int,
        max_topic_count: int,
        total_publishers_across_corpus: int,
    ) -> Tuple[int, str, str]:
        """
        Calculate transparent normalised priority score for Tata STRIVE (0 - 100).

        Weights:
        - Frequency (W_F = 0.30): Coverage volume vs maximum topic volume
        - Mission Relevance (W_R = 0.30): Strategic alignment with Tata STRIVE skilling pillars
        - Recency (W_Rec = 0.15): How recent the latest articles are
        - Historical Momentum (W_Mom = 0.15): Ratio of recent-half coverage vs older-half
        - Publisher Diversity (W_Div = 0.10): Spread across independent media outlets
        """
        count = len(articles)
        if count == 0:
            return 0, "Baseline", "momentum-stable"

        # 1. Frequency Score (0.0 to 1.0)
        s_freq = count / max(max_topic_count, 1)

        # 2. Mission Relevance Score (0.0 to 1.0)
        s_rel = topic.relevance_weight

        # 3. Recency Score (0.0 to 1.0)
        now_dt = datetime.now(timezone.utc)
        newest_article = max(articles, key=lambda a: a.created_at)
        days_old = max(0.0, (now_dt - newest_article.created_at).total_seconds() / 86400.0)
        s_rec = 1.0 / (1.0 + (days_old / 14.0))  # Half-life of 14 days

        # 4. Momentum Score & Classification (0.0 to 1.0)
        if len(articles) >= 4:
            sorted_dates = sorted([a.created_at for a in articles])
            mid_idx = len(sorted_dates) // 2
            first_half_span = (sorted_dates[mid_idx] - sorted_dates[0]).total_seconds() or 1.0
            second_half_span = (sorted_dates[-1] - sorted_dates[mid_idx]).total_seconds() or 1.0
            
            rate_first = mid_idx / first_half_span
            rate_second = (len(sorted_dates) - mid_idx) / second_half_span
            ratio = rate_second / max(rate_first, 1e-6)

            if ratio >= 1.6:
                s_mom = 0.95
                momentum_label = "Accelerating"
                momentum_badge = "positive"
            elif ratio >= 1.1:
                s_mom = 0.75
                momentum_label = "Consistent"
                momentum_badge = "positive"
            elif ratio <= 0.6:
                s_mom = 0.40
                momentum_label = "Cooling"
                momentum_badge = "negative"
            else:
                s_mom = 0.60
                momentum_label = "Steady"
                momentum_badge = "neutral"
        else:
            s_mom = 0.50
            momentum_label = "Baseline"
            momentum_badge = "neutral"

        # 5. Publisher Diversity Score (0.0 to 1.0)
        distinct_pubs = len(set(a.author.strip() for a in articles if a.author))
        s_div = min(1.0, distinct_pubs / max(min(total_publishers_across_corpus, 6), 1))

        # Composite Score Calculation
        score_val = (
            (0.30 * s_freq)
            + (0.30 * s_rel)
            + (0.15 * s_rec)
            + (0.15 * s_mom)
            + (0.10 * s_div)
        )
        final_score = int(round(score_val * 100))
        final_score = max(5, min(100, final_score))

        return final_score, momentum_label, momentum_badge

    def build_time_series(self, articles: list[Mention]) -> list[TopicTimeSeriesPoint]:
        """Aggregate unique articles by publication date and topic for the momentum chart."""
        if not articles:
            return []

        date_topic_counts: dict[str, dict[str, int]] = defaultdict(lambda: Counter())

        for a in articles:
            topic = self.categorize_article(a)
            # Use actual publication date
            d_str = a.created_at.strftime("%Y-%m-%d")
            date_topic_counts[d_str][topic.name] += 1

        points: list[TopicTimeSeriesPoint] = []
        for d_str in sorted(date_topic_counts.keys()):
            counts = date_topic_counts[d_str]
            total_on_date = sum(counts.values())
            points.append(
                TopicTimeSeriesPoint(
                    date=d_str,
                    topic_counts=dict(counts),
                    total_articles=total_on_date,
                )
            )

        return points

    def generate_recommendations(
        self,
        ranked_topics: list[TopicMetric],
        total_unique: int,
    ) -> list[AIRecommendation]:
        """Generate grounded, actionable communication and campaign recommendations."""
        recommendations: list[AIRecommendation] = []

        for t in ranked_topics[:4]:
            if t.article_count == 0:
                continue

            lead_article = t.supporting_articles[0] if t.supporting_articles else None
            evidence_url = lead_article.url if lead_article else "https://tatastrive.com"
            evidence_title = lead_article.title if lead_article else "Recent verified news report"
            evidence_pub = lead_article.author if lead_article else "Verified Media"

            if t.key == "tata_strive":
                rec = AIRecommendation(
                    topic=t.name,
                    priority_score=t.priority_score,
                    communication_objective="Amplify direct Tata STRIVE brand milestones and CSR partner co-creations.",
                    campaign_idea="Stories of Striving: Centre Showcase & Alumni Spotlight",
                    content_concept="Publish a multi-slide carousel and video short spotlighting recent graduates from the featured TSSDC centre with verified placement statistics.",
                    target_audience="CSR funding partners, corporate recruiters, and aspiring vocational youth.",
                    suggested_hashtags=["#TataSTRIVE", "#SkillingIndia", "#YouthEmpowerment", "#TataTrusts"],
                    evidence_headline=evidence_title,
                    evidence_publisher=evidence_pub,
                    evidence_url=evidence_url,
                )
            elif t.key == "skill_development":
                rec = AIRecommendation(
                    topic=t.name,
                    priority_score=t.priority_score,
                    communication_objective="Position Tata STRIVE as India's premier standard for hands-on, industry-certified vocational training.",
                    campaign_idea="Beyond Theory: Why Modern Industry Needs Certified Hands",
                    content_concept="Demystify technical domain careers (e.g., electrical, hospitality, healthcare) with visual infographics demonstrating starting salary trajectories and career ladders.",
                    target_audience="High school graduates, ITI aspirants, and parents seeking secure livelihood paths.",
                    suggested_hashtags=["#VocationalSkills", "#SkillDevelopment", "#HandsOnTraining", "#FutureReady"],
                    evidence_headline=evidence_title,
                    evidence_publisher=evidence_pub,
                    evidence_url=evidence_url,
                )
            elif t.key == "youth_employment":
                rec = AIRecommendation(
                    topic=t.name,
                    priority_score=t.priority_score,
                    communication_objective="Address youth anxiety regarding placement security and the gap between degrees and jobs.",
                    campaign_idea="From Learner to Earner: The Placement Guarantee Standard",
                    content_concept="Share authentic testimonials contrasting conventional degree struggles with Tata STRIVE's structured placement facilitation model.",
                    target_audience="First-time job seekers, freshers, and state skill mission coordinators.",
                    suggested_hashtags=["#YouthEmployment", "#JobPlacement", "#Livelihoods", "#TataSTRIVEPlacements"],
                    evidence_headline=evidence_title,
                    evidence_publisher=evidence_pub,
                    evidence_url=evidence_url,
                )
            elif t.key == "digital_skills":
                rec = AIRecommendation(
                    topic=t.name,
                    priority_score=t.priority_score,
                    communication_objective="Demystify AI, cloud, and digital tools for non-metro youth without engineering backgrounds.",
                    campaign_idea="Demystifying Digital: AI & Tech Careers for Every Youth",
                    content_concept="Step-by-step breakdown explaining that beginner digital tracks do not require coding genius, showcasing accessible Tata STRIVE tech courses.",
                    target_audience="Non-metro tier-2/3 youth, female learners, and career switchers.",
                    suggested_hashtags=["#DigitalSkills", "#AISkilling", "#TechCareers", "#InclusiveSkilling"],
                    evidence_headline=evidence_title,
                    evidence_publisher=evidence_pub,
                    evidence_url=evidence_url,
                )
            elif t.key == "career_readiness":
                rec = AIRecommendation(
                    topic=t.name,
                    priority_score=t.priority_score,
                    communication_objective="Promote the critical role of soft skills and the Youth Development Module (YDM) in corporate interviews.",
                    campaign_idea="The 5-Minute Interview Fix: Life Skills that Win the Job",
                    content_concept="Bite-sized Instagram and LinkedIn tips on body language, professional communication, and self-confidence taught in STRIVE centres.",
                    target_audience="Freshers preparing for their first corporate or service-sector interview.",
                    suggested_hashtags=["#CareerReadiness", "#InterviewPrep", "#LifeSkills", "#YouthDevelopmentModule"],
                    evidence_headline=evidence_title,
                    evidence_publisher=evidence_pub,
                    evidence_url=evidence_url,
                )
            else:
                rec = AIRecommendation(
                    topic=t.name,
                    priority_score=t.priority_score,
                    communication_objective=f"Align Tata STRIVE communications with trending national discourse around {t.name}.",
                    campaign_idea=f"Skilling India Perspective: Insights on {t.name}",
                    content_concept=f"Executive point-of-view commentary connecting national policy debates on {t.name} to grassroots community impact.",
                    target_audience="Policy stakeholders, skilling researchers, and institutional leaders.",
                    suggested_hashtags=["#SkillingMission", "#IndiaGrowth", "#Livelihoods"],
                    evidence_headline=evidence_title,
                    evidence_publisher=evidence_pub,
                    evidence_url=evidence_url,
                )

            recommendations.append(rec)

        return recommendations

    def analyze(
        self,
        mentions: list[Mention],
        *,
        date_range: str = "all",
        source_filter: str | None = None,
        query: str | None = None,
        project_id: int | None = None,
    ) -> TopicIntelligencePayload:
        """Run the end-to-end Topic Intelligence analysis pipeline with caching."""
        # Compute deterministic cache fingerprint
        raw_article_ids = sorted([m.id for m in mentions if m.record_type == "article" or m.source in {"rss", "gnews"}])
        corpus_hash = hashlib.sha256(",".join(raw_article_ids).encode("utf-8")).hexdigest()[:16]
        cache_key = f"{date_range}:{source_filter or 'all'}:{query or ''}:{project_id or ''}:{corpus_hash}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 1. Filter raw mentions by source if requested
        articles_to_process: list[Mention] = []
        for m in mentions:
            if m.record_type != "article" and m.source not in {"rss", "gnews"}:
                continue
            if source_filter and source_filter.lower() not in {"all", ""}:
                if m.source.lower() != source_filter.lower():
                    continue
            articles_to_process.append(m)

        # 2. Filter by date range (relative to latest article in database)
        if articles_to_process and date_range in {"7d", "30d", "90d"}:
            days_window = {"7d": 7, "30d": 30, "90d": 90}[date_range]
            # Use max date in corpus as reference anchor
            max_dt = max(a.created_at for a in articles_to_process)
            min_dt = max_dt.timestamp() - (days_window * 86400)
            articles_to_process = [
                a for a in articles_to_process if a.created_at.timestamp() >= min_dt
            ]

        # 3. Deduplicate articles
        deduped_articles, dedup_stats = self.deduplicate_articles(articles_to_process)
        total_unique = len(deduped_articles)

        # If zero or insufficient articles, construct clean insufficient-data payload
        if total_unique == 0:
            return TopicIntelligencePayload(
                generated_at=datetime.now(timezone.utc).isoformat(),
                filters_applied={"date_range": date_range, "source": source_filter, "query": query, "project_id": project_id},
                deduplication=dedup_stats,
                summary_cards={
                    "total_unique": 0,
                    "distinct_topics": 0,
                    "top_topic": "Insufficient Data",
                    "top_topic_share": 0.0,
                    "highest_priority": "Insufficient Data",
                    "highest_priority_score": 0,
                },
                segments=[],
                priority_topics=[],
                time_series=[],
                all_topic_names=[t.name for t in self.topics],
                recommendations=[],
                scoring_methodology={
                    "weights": {"frequency": 0.30, "relevance": 0.30, "recency": 0.15, "momentum": 0.15, "diversity": 0.10},
                    "formula": "Priority Score = round(100 * (0.30*Freq + 0.30*Rel + 0.15*Rec + 0.15*Mom + 0.10*Div))",
                    "note": "Derived strictly from collected verified media coverage, not empirical public opinion.",
                },
                articles_by_topic={},
            )

        # 4. Classify each unique article into exactly one primary topic
        topic_articles_map: dict[str, list[Mention]] = defaultdict(list)
        topic_counts: dict[str, int] = Counter()

        for a in deduped_articles:
            assigned_topic = self.categorize_article(a)
            topic_articles_map[assigned_topic.key].append(a)
            topic_counts[assigned_topic.key] += 1

        # Calculate exact percentages totaling 100.0%
        percentages = self.calculate_percentages(topic_counts, total_unique)
        max_count = max(topic_counts.values(), default=1)
        total_publishers = dedup_stats.unique_publishers_count

        # 5. Build TopicMetric structures & priority ranking
        ranked_topics: list[TopicMetric] = []
        articles_by_topic_dict: dict[str, list[dict[str, Any]]] = {}

        for topic in self.topics:
            t_articles = topic_articles_map.get(topic.key, [])
            count = len(t_articles)
            pct = percentages.get(topic.key, 0.0)

            # Convert to displayable article views
            article_views: list[TopicArticleView] = []
            for a in t_articles:
                article_views.append(
                    TopicArticleView(
                        id=a.id,
                        title=a.title or "Untitled News Article",
                        author=a.author or "Verified Media Publisher",
                        source=a.source,
                        url=a.url or "",
                        published_date=a.created_at.strftime("%d %b %Y"),
                        published_iso=a.created_at.isoformat(),
                        snippet=a.text[:240] + ("…" if len(a.text) > 240 else ""),
                        query=a.query,
                    )
                )

            articles_by_topic_dict[topic.name] = [asdict(av) for av in article_views]

            if count > 0:
                p_score, mom_label, mom_badge = self.calculate_priority_score(
                    topic=topic,
                    articles=t_articles,
                    total_unique_articles=total_unique,
                    max_topic_count=max_count,
                    total_publishers_across_corpus=total_publishers,
                )
                pubs = sorted(list(set(a.author.strip() for a in t_articles if a.author)))
                latest_date_str = max(a.created_at for a in t_articles).strftime("%d %b %Y")

                ranked_topics.append(
                    TopicMetric(
                        key=topic.key,
                        name=topic.name,
                        color=topic.color,
                        description=topic.description,
                        article_count=count,
                        percentage_share=pct,
                        relevance_weight=topic.relevance_weight,
                        relevance_score_pct=int(round(topic.relevance_weight * 100)),
                        priority_score=p_score,
                        momentum_label=mom_label,
                        momentum_badge=mom_badge,
                        publisher_count=len(pubs),
                        publishers=pubs[:4],
                        latest_date=latest_date_str,
                        supporting_articles=article_views,
                        explanation=topic.priority_rationale,
                    )
                )

        # Sort priority topics by priority_score descending
        priority_topics_sorted = sorted(ranked_topics, key=lambda t: t.priority_score, reverse=True)
        # Sort pie chart segments by count descending
        segments_sorted = sorted(ranked_topics, key=lambda t: t.article_count, reverse=True)

        # 6. Build Time-Series Points for Topic Momentum Chart
        time_series_points = self.build_time_series(deduped_articles)

        # 7. Generate Recommendations
        recommendations = self.generate_recommendations(priority_topics_sorted, total_unique)

        # 8. Compute Summary Cards
        top_topic = segments_sorted[0] if segments_sorted else None
        highest_priority = priority_topics_sorted[0] if priority_topics_sorted else None

        summary_cards = {
            "total_unique": total_unique,
            "raw_collected": dedup_stats.total_raw_articles,
            "duplicates_filtered": dedup_stats.duplicates_removed,
            "distinct_topics": len(segments_sorted),
            "top_topic": top_topic.name if top_topic else "N/A",
            "top_topic_share": top_topic.percentage_share if top_topic else 0.0,
            "top_topic_count": top_topic.article_count if top_topic else 0,
            "highest_priority": highest_priority.name if highest_priority else "N/A",
            "highest_priority_score": highest_priority.priority_score if highest_priority else 0,
            "unique_publishers": total_publishers,
        }

        scoring_methodology = {
            "weights": {
                "frequency": 0.30,
                "relevance": 0.30,
                "recency": 0.15,
                "momentum": 0.15,
                "diversity": 0.10,
            },
            "formula": (
                "Priority Score = round(100 * (0.30*Frequency_Norm + 0.30*Relevance_Weight + "
                "0.15*Recency_Decay + 0.15*Velocity_Ratio + 0.10*Publisher_Diversity))"
            ),
            "note": (
                "Priority ranking measures news editorial prominence and strategic relevance to Tata STRIVE's "
                "skilling and placement mandate. It is not an empirical survey of public opinion."
            ),
        }

        # Convert dataclasses to dicts for clean serialization
        segments_data = [
            {
                "key": t.key,
                "name": t.name,
                "color": t.color,
                "count": t.article_count,
                "article_count": t.article_count,
                "share": t.percentage_share,
                "percentage_share": t.percentage_share,
                "description": t.description,
                "latest_date": t.latest_date,
                "publisher_count": t.publisher_count,
                "publishers": t.publishers,
            }
            for t in segments_sorted
        ]

        priority_data = [
            {
                "key": t.key,
                "name": t.name,
                "topic": t.name,
                "color": t.color,
                "priority_score": t.priority_score,
                "article_count": t.article_count,
                "count": t.article_count,
                "share": t.percentage_share,
                "percentage_share": t.percentage_share,
                "relevance_score": t.relevance_score_pct,
                "relevance_score_pct": t.relevance_score_pct,
                "momentum_label": t.momentum_label,
                "momentum_badge": t.momentum_badge,
                "publisher_count": t.publisher_count,
                "publishers": t.publishers,
                "latest_date": t.latest_date,
                "explanation": t.explanation,
            }
            for t in priority_topics_sorted
        ]

        time_series_data = [
            {
                "date": p.date,
                "topic_counts": p.topic_counts,
                "total": p.total_articles,
            }
            for p in time_series_points
        ]

        rec_data = [asdict(r) for r in recommendations]

        payload = TopicIntelligencePayload(
            generated_at=datetime.now(timezone.utc).isoformat(),
            filters_applied={
                "date_range": date_range,
                "source": source_filter or "all",
                "query": query,
                "project_id": project_id,
            },
            deduplication=dedup_stats,
            summary_cards=summary_cards,
            segments=segments_data,
            priority_topics=priority_data,
            time_series=time_series_data,
            all_topic_names=[t.name for t in self.topics if t.name in topic_counts],
            recommendations=rec_data,
            scoring_methodology=scoring_methodology,
            articles_by_topic=articles_by_topic_dict,
        )

        self._cache[cache_key] = payload
        return payload


# Global singleton engine instance
_ENGINE_INSTANCE: Optional[TopicIntelligenceEngine] = None

def get_topic_engine() -> TopicIntelligenceEngine:
    global _ENGINE_INSTANCE
    if _ENGINE_INSTANCE is None:
        _ENGINE_INSTANCE = TopicIntelligenceEngine()
    return _ENGINE_INSTANCE
