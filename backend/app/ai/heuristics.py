"""Offline engine: deterministic, rule-based stand-ins for both agents.

Used when there is no API key, when the graduate has switched AI matching off,
or when a Claude call fails. Output shapes match the Claude schemas exactly.
"""

import re

from .schemas import (
    AdvisorResult,
    CVProfile,
    Experience,
    Insight,
    Match,
    MatchResult,
    OpportunityDraft,
    PlanStep,
    Suggestion,
)

SKILL_VOCAB = [
    "Python", "JavaScript", "TypeScript", "React", "HTML", "CSS", "SQL", "Excel", "Power BI", "Tableau",
    "Figma", "Canva", "Photoshop", "WordPress", "Shopify", "Squarespace", "SEO", "Google Analytics",
    "Social media", "Copywriting", "Photography", "Video editing", "Customer service", "Sales",
    "Bookkeeping", "Xero", "QuickBooks", "Data analysis", "Data cleaning", "Statistics", "R", "MATLAB",
    "CAD", "SolidWorks", "AutoCAD", "Project management", "Scheduling", "Research", "Presentation",
    "Teamwork", "Cash handling", "Stock control", "Health and safety", "Report writing", "Java", "C++",
    "Machine learning", "UX research", "Marketing", "Event planning", "Process mapping", "Spanish", "French",
]

_TRANSFERABLE = {
    "cafe": "Your hospitality work shows you can stay calm with queues, handle customers and money, and work as a team on busy shifts.",
    "café": "Your hospitality work shows you can stay calm with queues, handle customers and money, and work as a team on busy shifts.",
    "barista": "Barista shifts show reliability, speed under pressure and a feel for what customers want.",
    "retail": "Retail work shows customer focus, stock awareness and reliability.",
    "care": "Care work shows responsibility, empathy and careful record keeping.",
    "tutor": "Tutoring shows you can explain things clearly — useful for handover and training.",
    "warehouse": "Warehouse work shows reliability, safety awareness and process discipline.",
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9+#]", "", s.lower())


def _overlap(have: list[str], want: list[str]) -> list[str]:
    have_n = [_norm(h) for h in have]
    hits = []
    for w in want:
        wn = _norm(w)
        if any(wn and (wn in h or h in wn) for h in have_n if h):
            hits.append(w)
    return hits


# ---------------- Agent 1 (graduate) ----------------
def match(profile: dict, candidates: list[dict]) -> MatchResult:
    skills = profile.get("skills", [])
    exp_text = " ".join(f"{e.get('title','')} {e.get('organisation','')} {e.get('summary','')}" for e in profile.get("experiences", [])).lower()
    interests = " ".join(profile.get("interests", [])).lower()
    transferable = next((v for k, v in _TRANSFERABLE.items() if k in exp_text), "Your experience to date shows reliability and the ability to learn quickly on the job.")

    matches = []
    for opp in candidates:
        req, nice = opp["skills_required"], opp["skills_nice"]
        hit_req, hit_nice = _overlap(skills, req), _overlap(skills, nice)
        score = 35 + int(40 * len(hit_req) / max(len(req), 1)) + int(12 * len(hit_nice) / max(len(nice), 1))
        if any(word in interests for word in opp["firm"]["sector"].lower().split()):
            score += 6
        dist = opp.get("distance_miles")
        if dist is not None:
            score += 7 if dist <= 5 else 3 if dist <= 12 else 0
        score = max(10, min(score, 95))
        reasons = [f"You list {', '.join(hit_req[:3])}, which this role needs." if hit_req else "The role is entry-level and trains you on the core skills."]
        if hit_nice:
            reasons.append(f"Bonus skills you already have: {', '.join(hit_nice[:3])}.")
        if dist is not None:
            reasons.append(f"It's in {profile.get('home_area')} — no commute to speak of." if dist < 1 else f"It's {dist} miles from {profile.get('home_area')} — local and commutable.")
        matches.append(Match(
            opportunity_id=opp["id"],
            fit_score=score,
            headline=f"{opp['type_label']} at {opp['firm']['name']} that uses your {hit_req[0] if hit_req else 'transferable'} skills",
            reasons=reasons,
            skill_gaps=[s for s in req if s not in hit_req][:3],
            transferable_experience=transferable,
            career_path=f"Start here, then grow into a junior {opp['firm']['sector'].lower()} role with a North East employer.",
        ))
    matches.sort(key=lambda m: m.fit_score, reverse=True)
    top = skills[:4]
    return MatchResult(
        profile_summary=f"{profile.get('degree') or 'Graduate'} with strengths in {', '.join(top) if top else 'transferable skills'}, looking locally around {profile.get('home_area')}.",
        strengths=top or ["Reliability", "Willingness to learn"],
        matches=matches,
    )


def cv_profile(cv_text: str) -> CVProfile:
    found = [s for s in SKILL_VOCAB if re.search(rf"(?<![a-z]){re.escape(s.lower())}(?![a-z])", cv_text.lower())]
    experiences = []
    for line in cv_text.splitlines():
        m = re.match(r"\s*(.+?)\s+(?:at|@|-|–)\s+(.+?)\s*\(?((?:19|20)\d\d.*?)\)?\s*$", line)
        if m and len(experiences) < 4:
            experiences.append(Experience(title=m.group(1)[:60], organisation=m.group(2)[:60], period=m.group(3)[:30], summary=""))
    return CVProfile(
        headline="Recent graduate based in the North East",
        summary="Profile drafted from your CV with the offline engine. Review and edit before saving.",
        skills=found[:12],
        experiences=experiences,
        interests=[],
    )


# ---------------- Agent 2 (business owner) ----------------
_TEMPLATES: dict[str, dict] = {
    "website": dict(
        keywords=["website", "web", "online", "order", "menu", "google", "booking", "book", "ecommerce", "shop"],
        suggestion=("Launch a simple website with online ordering", "Give customers one place to see your menu/services and order or book without calling.", "You have strong word of mouth but customers can't act on it online.", "medium"),
        draft=dict(
            title="Website & online ordering build",
            type="paid_project",
            summary="Design and launch a fast, mobile-first website with menu/services, opening hours and an online ordering or booking flow the team can update themselves.",
            tasks=["Audit how customers currently find and contact the business", "Design a mobile-first site using a no-code builder", "Set up online ordering/booking and payments", "Connect Google Business Profile and Instagram", "Write a one-page guide so staff can update it"],
            skills_required=["HTML/CSS or a website builder", "Basic UX design", "Clear written communication"],
            skills_nice=["Figma", "SEO", "Photography"],
            removed=["Computer science degree", "2+ years' agency experience"],
            measures=["Site live by week 6", "Online orders/bookings tracked weekly", "Owner can update the menu without help"],
            hours=15, weeks=8,
            question="Show us a website (yours, a friend's, a club's, or a mock-up) and tell us one change you'd make to help a busy small business take orders online.",
        ),
    ),
    "marketing": dict(
        keywords=["instagram", "social", "marketing", "customers", "footfall", "brand", "reviews", "tiktok", "advertising", "quiet"],
        suggestion=("Turn great reviews into regular social content", "Post 3 times a week and reply to every review to convert reputation into visits.", "Reviews are strong but social activity is irregular.", "low"),
        draft=dict(
            title="Social media & content assistant",
            type="part_time",
            summary="Plan, shoot and post regular content, reply to reviews and report which posts bring customers in.",
            tasks=["Create a monthly content calendar", "Shoot photos/short videos on site", "Reply to reviews within 48 hours", "Report reach and enquiries monthly"],
            skills_required=["Social media", "Photography or video", "Copywriting"],
            skills_nice=["Canva", "Basic analytics"],
            removed=["Marketing degree"],
            measures=["12 posts a month", "Review reply rate above 90%", "Monthly report of enquiries from social"],
            hours=10, weeks=12,
            question="Pick a local business you like on Instagram. What's one post idea that would get more people through their door, and why?",
        ),
    ),
    "data": dict(
        keywords=["data", "spreadsheet", "excel", "paper", "records", "report", "quality", "tracking", "invoice", "stock", "dashboard"],
        suggestion=("Digitise paper records into one tracker", "Move key records into a shared sheet or simple database with a weekly dashboard.", "Paper and scattered spreadsheets make it hard to see problems early.", "medium"),
        draft=dict(
            title="Data clean-up & dashboard project",
            type="paid_project",
            summary="Clean and combine existing records into one structured tracker and build a simple weekly dashboard the team actually uses.",
            tasks=["Map where data lives today", "Design one clean structure", "Clean and migrate historical records", "Build a weekly dashboard", "Train the team and document the process"],
            skills_required=["Excel or Google Sheets", "Data cleaning", "Attention to detail"],
            skills_nice=["SQL", "Power BI", "Python"],
            removed=["Data science degree", "Industry experience"],
            measures=["All records in one place by week 5", "Dashboard reviewed weekly by the owner", "Time spent on reporting halved"],
            hours=15, weeks=8,
            question="Describe a time you turned messy information (a spreadsheet, notes, survey results) into something useful. What did you do first?",
        ),
    ),
    "operations": dict(
        keywords=["rota", "schedule", "staff", "shift", "process", "slow", "admin", "workflow", "time", "phone"],
        suggestion=("Map and simplify one painful process", "Document the current process, remove duplicate steps and automate the repetitive parts.", "Admin time is pulling the owner away from customers.", "low"),
        draft=dict(
            title="Process & scheduling improvement project",
            type="paid_project",
            summary="Map one time-consuming process (such as rotas or job scheduling), redesign it and set up a simple tool to run it.",
            tasks=["Shadow the team and map the current process", "Identify bottlenecks and duplicate steps", "Prototype a simpler workflow or tool", "Pilot for two weeks and measure time saved", "Hand over with clear documentation"],
            skills_required=["Process mapping", "Spreadsheets", "Clear communication"],
            skills_nice=["Project management", "No-code tools"],
            removed=["Operations management experience"],
            measures=["Current process mapped by week 2", "Pilot running by week 5", "Hours saved per week measured"],
            hours=12, weeks=8,
            question="Tell us about a task you made faster or easier — at work, uni or home. What was slowing it down?",
        ),
    ),
    "people": dict(
        keywords=["hire", "recruit", "turnover", "retention", "careers", "training", "onboarding"],
        suggestion=("Create a simple careers page and onboarding pack", "Make it easy to apply and quicker for new starters to get up to speed.", "Recruiting is slow and new starters take time to settle.", "low"),
        draft=dict(
            title="Recruitment & onboarding assistant",
            type="part_time",
            summary="Build a careers page, an onboarding pack and a simple tracker for applicants and new starters.",
            tasks=["Interview staff about what helped them settle", "Write an onboarding pack", "Publish a careers page", "Set up an applicant tracker"],
            skills_required=["Written communication", "Organisation"],
            skills_nice=["Canva", "WordPress"],
            removed=["HR qualification"],
            measures=["Onboarding pack in use", "Time-to-hire tracked"],
            hours=10, weeks=10,
            question="What would have helped you most in your first week at a new job or placement?",
        ),
    ),
}


def _pick_theme(text: str) -> str:
    text = text.lower()
    scores = {k: sum(text.count(w) for w in t["keywords"]) for k, t in _TEMPLATES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "operations"


def _draft(theme: str, firm_name: str) -> OpportunityDraft:
    d = _TEMPLATES[theme]["draft"]
    weeks = d["weeks"]
    half = max(2, weeks // 4)
    plan = [
        PlanStep(weeks=f"1-{half}", focus="Discovery: shadow the team, understand the problem", outcome="Agreed scope and success measures"),
        PlanStep(weeks=f"{half + 1}-{half * 2}", focus="Design and first version", outcome="Prototype reviewed with the owner and mentor"),
        PlanStep(weeks=f"{half * 2 + 1}-{weeks - 1}", focus="Build, test and iterate", outcome="Working solution in daily use"),
        PlanStep(weeks=f"{weeks}", focus="Handover and documentation", outcome="Team can run it without the student"),
    ]
    return OpportunityDraft(
        title=d["title"], type=d["type"], summary=d["summary"], tasks=d["tasks"], plan=plan,
        skills_required=d["skills_required"], skills_nice=d["skills_nice"], removed_requirements=d["removed"],
        success_measures=d["measures"], hours_per_week=d["hours"], weeks=weeks, role_question=d["question"],
        reasoning=f"A defined, time-boxed scope suits a graduate at {firm_name}: clear output, fortnightly mentor check-ins and no need for prior industry experience.",
    )


def advise(firm_ctx: dict, prompt: str) -> AdvisorResult:
    theme = _pick_theme(prompt + " " + firm_ctx.get("description", ""))
    t = _TEMPLATES[theme]
    title, rec, why, effort = t["suggestion"]
    other = [k for k in _TEMPLATES if k != theme][:2]
    suggestions = [Suggestion(title=title, recommendation=rec, why=why, effort=effort)] + [
        Suggestion(title=_TEMPLATES[k]["suggestion"][0], recommendation=_TEMPLATES[k]["suggestion"][1], why=_TEMPLATES[k]["suggestion"][2], effort=_TEMPLATES[k]["suggestion"][3])
        for k in other
    ]
    return AdvisorResult(
        understanding=f"You described: “{prompt.strip()[:220]}”. The core issue looks like {theme}. A short, paid student project can fix the first part of it.",
        suggestions=suggestions,
        needs_hire=True,
        opportunity=_draft(theme, firm_ctx.get("name", "your firm")),
    )


def insights(firm_ctx: dict) -> list[Insight]:
    p = firm_ctx.get("profile", {})
    out: list[Insight] = []
    if not p.get("website"):
        out.append(Insight(category="digital", title="Customers can't find or order from you online",
            problem=f"{p.get('google_reviews', 'Many')} reviews at {p.get('google_rating', '4+')}★, but no website or online ordering.",
            recommendation="Launch a simple mobile-first website with online ordering/booking.",
            expected_impact="Capture demand you already have; small cafés typically see 10–20% of orders move online.",
            effort="medium", evidence="Profile: website = none, online ordering = none.", opportunity_type="paid_project", role_title="Website & online ordering build"))
    if p.get("records") in {"paper", "spreadsheets"}:
        out.append(Insight(category="data", title="Key records live on paper or scattered sheets",
            problem="It's hard to spot problems early or report quickly.", recommendation="Move records into one tracker with a weekly dashboard.",
            expected_impact="Faster reporting and earlier warning on quality or cash issues.", effort="medium",
            evidence=f"Profile: records = {p.get('records')}.", opportunity_type="paid_project", role_title="Data clean-up & dashboard project"))
    if p.get("social_posts_per_month", 0) < 6:
        out.append(Insight(category="marketing", title="Great reputation, quiet social channels",
            problem="Posting is irregular, so reviews aren't turning into repeat visits.", recommendation="Post 3× a week and reply to every review.",
            expected_impact="More repeat customers at very low cost.", effort="low",
            evidence=f"Profile: ~{p.get('social_posts_per_month', 0)} posts/month.", opportunity_type="part_time", role_title="Social media & content assistant"))
    if p.get("scheduling") in {"spreadsheet", "whiteboard", "paper"}:
        out.append(Insight(category="operations", title="Scheduling takes hours every week",
            problem="Rotas/jobs are planned manually.", recommendation="Pilot a simple scheduling tool and document the process.",
            expected_impact="Several owner hours back per week.", effort="low",
            evidence=f"Profile: scheduling = {p.get('scheduling')}.", opportunity_type="paid_project", role_title="Process & scheduling improvement project"))
    if not p.get("careers_page"):
        out.append(Insight(category="people", title="No easy way for local talent to find you",
            problem="Without a careers page, hiring relies on word of mouth.", recommendation="Publish a careers page and onboarding pack.",
            expected_impact="Faster hiring and better retention.", effort="low",
            evidence="Profile: careers page = none.", opportunity_type="part_time", role_title="Recruitment & onboarding assistant"))
    return out[:4]
