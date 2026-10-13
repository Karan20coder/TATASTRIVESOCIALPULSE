"""Strategic Topic Classifier and Evidence Extractor for Tata STRIVE Social Pulse AI.

Classifies posts, comments, news articles, and videos into Tata STRIVE's core strategic
domains with explainable confidence and evidence-based rationale.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple

from harken.models import Mention, Sentiment

CATEGORIES = [
    "Tata STRIVE Brand Mentions",
    "Skill Development & Programs",
    "Youth Employment & Careers",
    "Vocational & Technical Training",
    "Digital Skills & Job Readiness",
    "Career Readiness & Professional Dev",
    "Audience Questions & Feedback",
    "Government Skilling Initiatives",
    "General Industry Discussion",
]

# Strategic domain vocabulary patterns
_PATTERNS = {
    "Tata STRIVE Brand Mentions": [
        r"\btata\s+strive\b",
        r"\btatastrive\b",
        r"\btata\s+community\s+initiatives\b",
        r"\banita\s+rajan\b",
        r"\btata\s+trusts?\s+skill\b",
    ],
    "Audience Questions & Feedback": [
        r"\b(how\s+to\s+apply|eligibility|fees?|cost|free\s+training|free\s+course|admission|stipend)\b",
        r"\b(certificate|valid|fake|placement\s+guarantee|100%\s+placement|where\s+is|contact\s+number)\b",
        r"\b(complaint|delay|bad\s+experience|fraud|unhelpful|worth\s+it\?|can\s+i\s+join)\b",
    ],
    "Digital Skills & Job Readiness": [
        r"\b(digital\s+skills?|artificial\s+intelligence|ai|machine\s+learning|coding|python|data\s+analytics)\b",
        r"\b(cloud\s+computing|cybersecurity|web\s+dev|full\s+stack|software|it\s+skills?|tech\s+skills?)\b",
    ],
    "Vocational & Technical Training": [
        r"\b(vocational\s+training|iti|industrial\s+training|polytechnic|technician|electrician|welder)\b",
        r"\b(hospitality|healthcare\s+assist|automotive|carpenter|plumber|technical\s+trade|craftsman)\b",
    ],
    "Youth Employment & Careers": [
        r"\b(youth\s+employ|freshers?|campus\s+hiring|job\s+fair|placement|job\s+opportunities?|internship)\b",
        r"\b(unemployment|first\s+job|entry\s+level|career\s+guidance|campus\s+placement|employability)\b",
    ],
    "Career Readiness & Professional Dev": [
        r"\b(soft\s+skills?|resume|interview\s+prep|communication\s+skills?|workplace\s+readiness)\b",
        r"\b(professional\s+development|grooming|career\s+counseling|life\s+skills)\b",
    ],
    "Government Skilling Initiatives": [
        r"\b(ministry\s+of\s+skill\s+development|msde|nsdc|dgt|pmkvy|kaushal\s+vikas|skill\s+india)\b",
        r"\b(national\s+apprenticeship|naps|government\s+scheme|policy|budget\s+for\s+skill)\b",
    ],
    "Skill Development & Programs": [
        r"\b(skill\s+development|skilling|upskilling|reskilling|training\s+center|course\s+curriculum)\b",
        r"\b(vocational\s+education|skill\s+gap|future\s+of\s+work|capacity\s+building)\b",
    ],
}


@dataclass
class ClassificationResult:
    category: str
    confidence: float
    evidence: str
    sentiment_reason: str


class ContentClassifier:
    """Classifies content and extracts supporting evidence."""

    def classify(self, mention: Mention) -> ClassificationResult:
        blob = f"{mention.title or ''} {mention.text or ''}".lower()
        matched_category = "General Industry Discussion"
        best_score = 0
        evidence_phrases: list[str] = []

        # Brand match check gets highest priority
        for pat in _PATTERNS["Tata STRIVE Brand Mentions"]:
            m = re.search(pat, blob)
            if m:
                matched_category = "Tata STRIVE Brand Mentions"
                best_score = 10
                evidence_phrases.append(f"Mentioned brand '{m.group()}'")
                break

        # Check other categories
        if matched_category != "Tata STRIVE Brand Mentions":
            for cat, patterns in _PATTERNS.items():
                if cat == "Tata STRIVE Brand Mentions":
                    continue
                score = 0
                for pat in patterns:
                    matches = re.findall(pat, blob)
                    if matches:
                        score += len(matches) * 2
                        evidence_phrases.append(f"Found keyword '{matches[0]}'")
                if score > best_score:
                    best_score = score
                    matched_category = cat

        # Fallback to query intent
        if best_score == 0:
            q = mention.query.lower()
            if "strive" in q:
                matched_category = "Tata STRIVE Brand Mentions"
                evidence_phrases.append(f"Tracked term: {mention.query}")
            elif "youth" in q or "employ" in q:
                matched_category = "Youth Employment & Careers"
            elif "vocational" in q or "trade" in q:
                matched_category = "Vocational & Technical Training"
            elif "skill" in q:
                matched_category = "Skill Development & Programs"
            confidence = 0.70
        else:
            confidence = min(0.95, 0.75 + (best_score * 0.05))

        # Sentiment rationale / evidence
        sentiment_reason = _explain_sentiment(mention, blob)
        evidence_text = "; ".join(evidence_phrases[:3]) if evidence_phrases else "Matched general industry skilling context."

        return ClassificationResult(
            category=matched_category,
            confidence=round(confidence, 2),
            evidence=evidence_text,
            sentiment_reason=sentiment_reason,
        )


def _explain_sentiment(mention: Mention, text: str) -> str:
    """Build explainable rationale for assigned sentiment."""
    # News articles reporting factual developments are neutral reporting by default
    if mention.record_type == "article":
        if "award" in text or "launches" in text or "partnership" in text or "success" in text:
            return "Positive news coverage highlighting partnerships, program launches or awards."
        if "crisis" in text or "protest" in text or "drop" in text or "unemployment" in text:
            return "Neutral news reporting on labor market statistics and youth employment challenges."
        return "Objective news reporting on policy, institutional announcements and industry skilling."

    if mention.sentiment == Sentiment.POSITIVE:
        return "Audience expressed satisfaction, gratitude, or appreciation for skill training and job support."
    elif mention.sentiment == Sentiment.NEGATIVE:
        return "Audience raised complaints, questions, or frustration regarding access, delays, or eligibility."
    elif mention.sentiment == Sentiment.UNCERTAIN:
        return "Ambiguous or mixed tone with both inquiry and critical feedback."
    return "Neutral informational statement or standard course query without strong valence."
