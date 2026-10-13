"""Content and Campaign Copilot for Tata STRIVE Social Pulse AI.

Generates evidence-backed campaign briefs, multi-slide Instagram carousels,
short-form video scripts (YouTube Shorts/Reels), and platform-specific drafts
with built-in human verification safeguards.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from harken.models import Mention

# Official verified Tata STRIVE pillars (never hallucinated)
TATA_STRIVE_CORE_FACTS = """
Official Brand Context:
- Tata STRIVE is the skill development initiative of Tata Community Initiatives Trust (TCIT), under the aegis of Tata Trusts.
- Focus: Empowering youth from disadvantaged backgrounds with market-aligned technical and life skills.
- Key models: Tata STRIVE Skill Development Centres (TSSDC), ITI upgradation, institutional partnerships.
- Core pillars: Youth Development Module (YDM) for life skills, technical domain training, coach-led mentoring, placement facilitation.
- Official domain: https://tatastrive.com
- Human Verification Notice: Course fees, batch dates, centre addresses, and placement tie-ups must be verified against current TCIT program schedules before public release.
"""


@dataclass
class CampaignBrief:
    topic: str
    why_it_matters: str
    audience_need: str
    objective: str
    campaign_title: str
    carousel_outline: list[dict[str, str]]
    short_video_concept: dict[str, str]
    caption: str
    cta: str
    platform_variations: dict[str, str]
    measurement_kpis: list[str]
    supporting_urls: list[str]
    verification_guardrail: str


class CampaignCopilot:
    """Generates structured, grounded campaign briefs for the communications team."""

    def generate_brief(
        self,
        topic: str,
        mentions: list[Mention] | None = None,
        audience_question: str | None = None,
    ) -> CampaignBrief:
        mentions = mentions or []
        supporting_urls = [m.url for m in mentions if m.url and m.url.startswith(("http://", "https://"))][:5]

        # Template logic grounded in Tata STRIVE domains
        if "Digital" in topic or "Tech" in topic or "ai" in topic.lower():
            why_it_matters = "Rapid enterprise adoption of AI and cloud is widening the entry-level skills gap for non-metro freshers."
            audience_need = audience_question or "Clarity on entry barriers, required prerequisites, and beginner-friendly digital curricula."
            objective = "Demystify digital careers for first-generation learners and drive admissions for certified IT/digital batches."
            campaign_title = "#FutureReady: Bridge the Digital Career Divide with Tata STRIVE"
            carousel_outline = [
                {"slide": "1", "title": "Hook", "copy": "Think Tech Careers Require an Engineering Degree? Think Again."},
                {"slide": "2", "title": "Industry Reality", "copy": "Companies need certified skills in Python, Cloud, and Data Literacy — not just theory."},
                {"slide": "3", "title": "The Tata STRIVE Edge", "copy": "Hands-on project learning combined with the Youth Development Module (YDM) for corporate workplace etiquette."},
                {"slide": "4", "title": "Student Journey", "copy": "From foundational computer literacy to placement assistance with industry employers."},
                {"slide": "5", "title": "Next Step / CTA", "copy": "Find your nearest TSSDC centre or register online today at tatastrive.com."},
            ]
            short_video_concept = {
                "hook_0_5s": "Close-up on mobile screen scrolling job portals. Voiceover: 'Applied to 20 jobs and heard back from none?'",
                "core_5_30s": "Show transition into a vibrant Tata STRIVE computer lab. Mentor assisting learner: 'Employers look for practical industry certifications and real workplace confidence.'",
                "cta_30_45s": "Text on screen: 'Empower your future with Tata STRIVE. Check program eligibility today!'",
            }
            caption = (
                "The future of work is digital, and every passionate youth deserves a seat at the table. 🚀\n\n"
                "At Tata STRIVE, our courses blend in-demand tech foundations with essential workplace life skills to get you job-ready.\n\n"
                "👉 Tap the link in bio or visit tatastrive.com to explore upcoming digital batches in your region.\n\n"
                "#TataSTRIVE #DigitalSkills #SkillIndia #YouthEmployability #TechCareers #FutureReady"
            )
            cta = "Visit tatastrive.com or visit your nearest Tata STRIVE Skill Development Centre."
            platform_variations = {
                "Instagram": "Vibrant visual carousel focusing on student empowerment and practical lab training.",
                "LinkedIn": "Thought leadership post highlighting TCIT's public-private partnerships in digital skilling.",
                "YouTube Shorts": "Quick 45s myth-buster on starting a tech career without a CS degree.",
                "X": "High-impact 2-tweet thread on bridging India's digital skill divide with verifiable outcomes.",
            }
            measurement_kpis = [
                "Profile visits and CTA clicks to tatastrive.com/courses",
                "Direct inquiries regarding local centre admission dates",
                "Save and share rate on the educational carousel",
            ]

        elif "Brand" in topic or "STRIVE" in topic:
            why_it_matters = "Mainstream press and partners are highlighting Tata STRIVE's collaborative skilling milestones across India."
            audience_need = audience_question or "Understanding the pedigree, non-profit mission, and credibility of Tata STRIVE credentials."
            objective = "Reinforce brand trust, highlight corporate partner collaborations, and celebrate alumni employment milestones."
            campaign_title = "Skilling With Purpose: The Tata STRIVE Story"
            carousel_outline = [
                {"slide": "1", "title": "Hook", "copy": "Over A Decade of Empowering India's Youth: The Tata STRIVE Promise."},
                {"slide": "2", "title": "The Mission", "copy": "Transforming the skilling ecosystem through quality, scale, and dignity of labor."},
                {"slide": "3", "title": "The Pedigree", "copy": "An initiative of Tata Community Initiatives Trust under Tata Trusts, partnering with global industry leaders."},
                {"slide": "4", "title": "Holistic Model", "copy": "Not just technical training — our Youth Development Module builds life-long character and resilience."},
                {"slide": "5", "title": "Impact & CTA", "copy": "Join our skilling movement as a partner, learner, or mentor at tatastrive.com."},
            ]
            short_video_concept = {
                "hook_0_5s": "Montage of diverse youth walking proudly into work. 'What does real skilling look like?'",
                "core_5_30s": "Fast cuts of training sessions: hospitality, technical trades, digital labs, and smiling graduates receiving certifications.",
                "cta_30_45s": "Logo: Tata STRIVE. 'Right Skills. Bright Future. Discover our story.'",
            }
            caption = (
                "Empowerment begins with an opportunity. 🌱\n\n"
                "Through Tata STRIVE, we are committed to touching lives, building industry-aligned skills, and enabling dignified livelihoods for India's youth.\n\n"
                "Discover our journey, partner with our mission, or join a course near you at tatastrive.com.\n\n"
                "#TataSTRIVE #TataTrusts #SkillDevelopment #SkillingIndia #YouthEmpowerment"
            )
            cta = "Explore our impact stories and partner with us at tatastrive.com."
            platform_variations = {
                "Instagram": "Inspirational brand carousel with quote from TCIT leadership and partner logos.",
                "LinkedIn": "Corporate post highlighting corporate social responsibility (CSR) collaboration models.",
                "YouTube Shorts": "60-second celebration reel of alumni placed in reputable enterprises.",
                "X": "Celebratory milestone post highlighting partner certifications.",
            }
            measurement_kpis = [
                "Brand sentiment positivity index",
                "Inbound CSR partnership queries",
                "Alumni engagement and comment testimonials",
            ]

        else:
            # Employability / Vocational Training default
            why_it_matters = "Freshers and job seekers frequently inquire about practical training, fee structures, and genuine placement assistance."
            audience_need = audience_question or "Authentic information on course eligibility, fees (free training), and real placement support."
            objective = "Address frequent candidate questions with radical transparency and clear guidance on admissions."
            campaign_title = "FAQ Spotlight: Everything You Need to Know About Tata STRIVE Courses"
            carousel_outline = [
                {"slide": "1", "title": "Hook", "copy": "Your Top 4 Questions About Tata STRIVE Training Answered!"},
                {"slide": "2", "title": "Q1: Is Training Really Free / Subsidised?", "copy": "Yes! Tata STRIVE programs for eligible youth are philanthropic initiatives supported by TCIT and CSR partners."},
                {"slide": "3", "title": "Q2: Who is Eligible?", "copy": "Youth aged 18–35 (varies by trade), from 10th pass to graduates seeking job readiness."},
                {"slide": "4", "title": "Q3: Do You Provide Job Placement?", "copy": "We provide dedicated career coaching, interview prep, and facilitate recruitment drives with verified employers."},
                {"slide": "5", "title": "Q4: How Do I Apply?", "copy": "Visit tatastrive.com or visit your nearest Centre with your ID and educational documents."},
            ]
            short_video_concept = {
                "hook_0_5s": "Counselor speaking to camera: 'Are Tata STRIVE courses really free? Let me answer your top 3 questions.'",
                "core_5_30s": "Quick-fire Q&A graphics answering eligibility, placement support, and certificate validity.",
                "cta_30_45s": "'Have more questions? Drop them in the comments below or head over to tatastrive.com!'",
            }
            caption = (
                "Got questions about getting trained and job-ready? We have answers! 💡\n\n"
                "Swipe through our candidate FAQ guide covering eligibility, training domains, and placement facilitation.\n\n"
                "💬 Still have queries? Drop your question in the comments below — our team is here to guide you!\n\n"
                "#TataSTRIVE #YouthEmployment #VocationalTraining #CareerGuidance #SkillDevelopment"
            )
            cta = "Drop your questions in the comments or visit tatastrive.com."
            platform_variations = {
                "Instagram": "Carousel breaking down the 4 most asked student questions.",
                "LinkedIn": "Resource post aimed at career counselors and placement officers.",
                "YouTube Shorts": "30-second rapid-fire Q&A video featuring a Tata STRIVE facilitator.",
                "X": "Informative thread addressing admission myths.",
            }
            measurement_kpis = [
                "Candidate question resolution rate in comments",
                "Direct messages (DMs) requesting admission details",
                "Link clicks to course directory",
            ]

        verification_guardrail = (
            "[HUMAN VERIFICATION REQUIRED: Before publishing, verify exact batch commencement dates, "
            "centre locations, and eligibility criteria against current Tata STRIVE operational records. "
            "Never guarantee 100% placement or invent specific salary packages.]"
        )

        return CampaignBrief(
            topic=topic,
            why_it_matters=why_it_matters,
            audience_need=audience_need,
            objective=objective,
            campaign_title=campaign_title,
            carousel_outline=carousel_outline,
            short_video_concept=short_video_concept,
            caption=caption,
            cta=cta,
            platform_variations=platform_variations,
            measurement_kpis=measurement_kpis,
            supporting_urls=supporting_urls,
            verification_guardrail=verification_guardrail,
        )
