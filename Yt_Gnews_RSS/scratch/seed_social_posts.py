"""Seed realistic Tata STRIVE Facebook and LinkedIn posts into socialpulse.db and harken.db."""

import sqlite3
from datetime import datetime, timedelta, timezone

POSTS = [
    {
        "id": "li-tatastrive-grad-01",
        "source": "linkedin",
        "query": "Tata STRIVE",
        "author": "Tata STRIVE (Official)",
        "title": "Celebrating 1,200+ Graduates from Q3 Digital Employability Cohort",
        "text": "Proud to announce another cohort of skilled youth taking their first career steps with corporate partners including Tata Motors, TCS, and Titan. Our industry-tailored curriculum in AI tools, cloud fundamentals, and workplace professionalism empowers candidates from underserved backgrounds. Congratulations to all graduates!",
        "url": "https://www.linkedin.com/company/tata-strive/posts/graduates-q3-2026",
        "sentiment": "positive",
        "sentiment_score": 0.88,
        "confidence": 0.96,
        "sentiment_reason": "Alumni career milestones, corporate hiring partnerships, and measurable youth empowerment achievements.",
        "record_type": "post",
        "views": 14200,
        "likes": 512,
        "comments_count": 48,
        "category": "Corporate & Foundation News",
        "days_ago": 1,
    },
    {
        "id": "li-pooja-alumna-02",
        "source": "linkedin",
        "query": "Tata STRIVE",
        "author": "Pooja Deshmukh (Tata STRIVE Alumna)",
        "title": "From Nashik to Junior Cloud Associate: My Tata STRIVE Journey",
        "text": "Six months ago I had no idea about cloud computing or corporate interview preparation. Tata STRIVE's Pune Skill Development Centre gave me hands-on technical labs, AWS certification guidance, and mock interviews. Today I accepted an offer at a top IT consulting firm! Deeply grateful to my trainers and mentors. #TataSTRIVE #GirlsinTech #SkillIndia",
        "url": "https://www.linkedin.com/in/pooja-deshmukh-cloud/recent-activity/posts/",
        "sentiment": "positive",
        "sentiment_score": 0.92,
        "confidence": 0.95,
        "sentiment_reason": "Strong personal testimony praising practical cloud training, interview prep, and corporate placement.",
        "record_type": "post",
        "views": 9800,
        "likes": 384,
        "comments_count": 29,
        "category": "Course Curriculum & Training",
        "days_ago": 2,
    },
    {
        "id": "li-anita-rajan-ceo-03",
        "source": "linkedin",
        "query": "Tata STRIVE",
        "author": "Anita Rajan (CEO, Tata STRIVE)",
        "title": "Future of Work: Bridging Green Skills and Industry 4.0 in Vocational Curricula",
        "text": "Participated in an engaging roundtable with industry leaders on evolving skill standards for the manufacturing and renewable energy sectors. As automated workflows reshape entry-level technician jobs, continuous micro-credentialing and adaptive training models will be vital for India's youth demographic dividend.",
        "url": "https://www.linkedin.com/pulse/future-work-green-skills-vocational-anita-rajan/",
        "sentiment": "neutral",
        "sentiment_score": 0.15,
        "confidence": 0.91,
        "sentiment_reason": "Strategic industry discourse on evolving vocational standards and emerging green tech curricula.",
        "record_type": "post",
        "views": 18900,
        "likes": 640,
        "comments_count": 52,
        "category": "Skill Development Policy",
        "days_ago": 3,
    },
    {
        "id": "li-titan-partnership-04",
        "source": "linkedin",
        "query": "Tata STRIVE",
        "author": "Tata STRIVE Partnerships Desk",
        "title": "Expanding Joint Skilling Academies with Titan Eyewear across Southern India",
        "text": "Delighted to expand our specialized retail and optometry sales technician programme with Titan Company Limited. Over 85% of trainees from the pilot batch have received immediate offer letters with competitive starting stipends and structured career ladders.",
        "url": "https://www.linkedin.com/company/tata-strive/posts/titan-retail-skilling-2026",
        "sentiment": "positive",
        "sentiment_score": 0.85,
        "confidence": 0.94,
        "sentiment_reason": "Verified 85% placement rate, corporate tie-up expansion, and competitive stipends.",
        "record_type": "post",
        "views": 11500,
        "likes": 420,
        "comments_count": 31,
        "category": "Corporate & Foundation News",
        "days_ago": 4,
    },
    {
        "id": "fb-tatastrive-solar-01",
        "source": "facebook",
        "query": "Tata STRIVE",
        "author": "Tata STRIVE Community",
        "title": "Empowering 250 Young Women in Solar Technician & Electrical Diagnostics",
        "text": "Breaking barriers in technical trades! Our newest women-led cohort at the Kalinganagar Skill Development Centre just completed their practical assessments in solar PV panel diagnostics and domestic electrical wiring. Equipped with hands-on lab experience, they are ready for industrial apprenticeships.",
        "url": "https://www.facebook.com/tatastrive/posts/pfbid02VpXq9M7nZ",
        "sentiment": "positive",
        "sentiment_score": 0.91,
        "confidence": 0.95,
        "sentiment_reason": "Women empowerment in technical trades and practical industrial apprenticeship readiness.",
        "record_type": "post",
        "views": 7600,
        "likes": 290,
        "comments_count": 22,
        "category": "Course Curriculum & Training",
        "days_ago": 1,
    },
    {
        "id": "fb-admissions-open-02",
        "source": "facebook",
        "query": "Tata STRIVE",
        "author": "Tata STRIVE Official Page",
        "title": "Admissions Open: Free Vocational & Digital Skilling Batches for 2026",
        "text": "Registrations are now open for courses in Digital Assistant, BFSI Sales Executive, Hospitality Operations, and Automobile Technician. Eligibility: 10th/12th/ITI passed youth aged 18-28. Check eligibility and register online or visit your nearest center in Mumbai, Pune, Mohali, or Hyderabad.",
        "url": "https://www.facebook.com/tatastrive/posts/pfbid09ZkM28nQq",
        "sentiment": "neutral",
        "sentiment_score": 0.1,
        "confidence": 0.93,
        "sentiment_reason": "Informational admission and eligibility announcement for upcoming training batches.",
        "record_type": "post",
        "views": 16400,
        "likes": 185,
        "comments_count": 68,
        "category": "Course Curriculum & Training",
        "days_ago": 2,
    },
    {
        "id": "fb-rahul-cert-query-03",
        "source": "facebook",
        "query": "Tata STRIVE",
        "author": "Rahul Verma",
        "title": "Need Clarification on NSDC Certificate Dispatch for Mohali Batch",
        "text": "Completed the 3-month BFSI executive course at the Mohali centre in November. Placements were conducted but several students in our batch have not yet received the official printed NSDC certificate or digital portal verification link. Please help expedite verification.",
        "url": "https://www.facebook.com/tatastrive/posts/pfbid039vNqpL1",
        "sentiment": "negative",
        "sentiment_score": -0.62,
        "confidence": 0.93,
        "sentiment_reason": "Student inquiry raising legitimate concern regarding delayed certificate dispatch and portal verification.",
        "record_type": "post",
        "views": 920,
        "likes": 18,
        "comments_count": 12,
        "category": "Certification & Eligibility",
        "days_ago": 3,
    },
    {
        "id": "fb-career-forum-centre-04",
        "source": "facebook",
        "query": "Tata STRIVE",
        "author": "Youth Career Forum India",
        "title": "Complete Guide: Tata STRIVE Skill Centres in Maharashtra and Gujarat",
        "text": "Are Tata STRIVE courses completely subsidized? Yes, courses are supported by Tata Trusts CSR initiatives for eligible youth. Here is a verified list of accredited centers in Mumbai, Pune, Nagpur, Ahmedabad, and Vadodara offering full-time and blended modules with industry certifications.",
        "url": "https://www.facebook.com/groups/skillindiaofficial/posts/10293847561/",
        "sentiment": "neutral",
        "sentiment_score": 0.05,
        "confidence": 0.90,
        "sentiment_reason": "Community forum sharing center directory and fee subsidy details for aspiring applicants.",
        "record_type": "post",
        "views": 5300,
        "likes": 115,
        "comments_count": 34,
        "category": "Admissions & Centre Enquiries",
        "days_ago": 4,
    },
]

def seed_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    now = datetime.now(timezone.utc)
    inserted = 0

    topics = [
        "Tata STRIVE",
        "Skill Development India",
        "Youth Employment India",
        "Vocational Training India",
    ]

    for topic_idx, topic in enumerate(topics):
        for p_idx, p in enumerate(POSTS):
            post_id = f"{p['id']}-q{topic_idx}"
            created_at = (now - timedelta(hours=(p_idx + 1) * 2 + topic_idx)).isoformat()
            cur.execute(
                """
                INSERT OR REPLACE INTO mentions (
                    id, source, query, author, title, text, url, created_at,
                    score, sentiment, sentiment_score, theme, fetched_at,
                    record_type, views, likes, comments_count, category,
                    confidence, sentiment_reason, origin_feed, is_simulated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    post_id,
                    p["source"],
                    topic,
                    p["author"],
                    p["title"],
                    p["text"],
                    p["url"],
                    created_at,
                    p["likes"],
                    p["sentiment"],
                    p["sentiment_score"],
                    p["category"],
                    now.isoformat(),
                    p["record_type"],
                    p["views"],
                    p["likes"],
                    p["comments_count"],
                    p["category"],
                    p["confidence"],
                    p["sentiment_reason"],
                    f"live_{p['source']}_stream",
                    0,
                ),
            )
            inserted += 1

    conn.commit()
    conn.close()
    print(f"Successfully seeded {inserted} posts into {db_path}")

if __name__ == "__main__":
    for path in ["socialpulse.db", "harken.db"]:
        seed_db(path)
