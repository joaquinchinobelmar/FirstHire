"""Seed the prototype with SYNTHETIC data only (no real people, no real firms).

Run from /backend:   python -m app.seed

Demo passwords are generated randomly on first run, stored only as PBKDF2
hashes in the DB, and written in plain text to backend/DEMO_CREDENTIALS.local.md
(git-ignored) so the team can log in. They never reach the frontend.
"""

import json
import random
import secrets
from datetime import date, datetime, timedelta

from .config import BACKEND_DIR, settings
from .db import connect, dumps, init_db
from .security import hash_password

CRED_FILE = BACKEND_DIR / "DEMO_CREDENTIALS.local.md"
WORDS = ["tyne", "wear", "quay", "metro", "angel", "bridge", "castle", "harbour", "northern", "lantern", "coast", "valley"]

USERS = [
    # email, role, display name
    ("aisha.rahman@student.example", "graduate", "Aisha Rahman"),
    ("tom.hughes@student.example", "graduate", "Tom Hughes"),
    ("priya.nair@student.example", "graduate", "Priya Nair"),
    ("owner@tynestreetkitchen.example", "owner", "Daniel Okafor"),
    ("owner@quaysideprecision.example", "owner", "Helen Marsh"),
    ("owner@wearvalleycare.example", "owner", "Graham Lowes"),
]


def _password() -> str:
    return f"{secrets.choice(WORDS).capitalize()}-{secrets.choice(WORDS).capitalize()}-{secrets.randbelow(9000) + 1000}"


def _load_or_create_passwords() -> dict[str, str]:
    existing: dict[str, str] = {}
    if CRED_FILE.exists():
        for line in CRED_FILE.read_text(encoding="utf-8").splitlines():
            parts = [p.strip().strip("`") for p in line.split("|")]
            if len(parts) >= 5 and "@" in parts[1]:
                existing[parts[1]] = parts[3]
    passwords = {email: existing.get(email) or _password() for email, _, _ in USERS}
    lines = [
        "# FirstHire demo credentials (LOCAL ONLY — git-ignored, never commit or show in the UI)",
        "",
        "| Email | Role | Password | Name |",
        "|---|---|---|---|",
    ]
    for email, role, name in USERS:
        lines.append(f"| `{email}` | {role} | `{passwords[email]}` | {name} |")
    lines += ["", "All people and firms are synthetic. Re-run `python -m app.seed` to reset the demo (passwords are kept)."]
    CRED_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return passwords


# ---------------------------------------------------------------- firms
FIRMS = [
    dict(key="tsk", owner="owner@tynestreetkitchen.example", name="Tyne Street Kitchen Ltd", number="SYN04821", sic=["56102"],
         sector="Food & hospitality", town="Gateshead", postcode="NE8 1EP", employees=11, incorporated="2019-03-14",
         description="Busy independent street-food café near Gateshead Quays. Known for its Caribbean-Geordie lunch menu, catering for local offices, and long lunchtime queues.",
         profile=dict(website=None, online_ordering=False, bookings="phone and Instagram DMs", google_rating=4.8, google_reviews=640,
                      instagram_followers=3200, social_posts_per_month=3, card_payments=True, delivery_apps=False,
                      records="paper", scheduling="whiteboard", careers_page=False,
                      notes="Phone rings non-stop at lunch; regulars keep asking for a catering menu and pre-ordering. Owner does all admin at night.")),
    dict(key="qpe", owner="owner@quaysideprecision.example", name="Quayside Precision Engineering Ltd", number="SYN07733", sic=["25620"],
         sector="Manufacturing", town="Gateshead", postcode="NE11 0QD", employees=24, incorporated="2008-09-02",
         description="CNC machining and fabrication on Team Valley, supplying parts to offshore wind and automotive customers across the North East.",
         profile=dict(website="basic, last updated 2016", online_ordering=False, google_rating=4.4, google_reviews=31,
                      social_posts_per_month=0, records="paper", quality_records="paper job cards and Excel",
                      scheduling="spreadsheet", scrap_rate_pct=6.1, on_time_delivery_pct=84, careers_page=False, apprentices=2,
                      notes="Quality paperwork slows down audits; no live view of which jobs are late.")),
    dict(key="wvc", owner="owner@wearvalleycare.example", name="Wear Valley Care Partners", number="SYN05190", sic=["88100"],
         sector="Health & social care", town="Durham", postcode="DH1 3NJ", employees=38, incorporated="2014-05-21",
         description="Home-care provider supporting older people across County Durham with visits, companionship and reablement.",
         profile=dict(website="yes", online_ordering=False, google_rating=4.6, google_reviews=88, social_posts_per_month=2,
                      records="spreadsheets", scheduling="spreadsheet", careers_page=False, staff_turnover_pct=31,
                      notes="Rota changes take the manager ~10 hours a week; recruitment relies on word of mouth.")),
    dict(key="nla", name="Northern Ledger Accountants", number="SYN03312", sic=["69201"], sector="Professional services",
         town="Newcastle upon Tyne", postcode="NE1 6SQ", employees=9, incorporated="2011-01-10",
         description="Small accountancy practice serving sole traders and SMEs across Tyneside.", profile=dict(website="yes")),
    dict(key="ocs", name="Ouseburn Creative Studio", number="SYN06654", sic=["73110"], sector="Creative & marketing",
         town="Newcastle upon Tyne", postcode="NE6 1BU", employees=7, incorporated="2017-06-30",
         description="Design and content studio working with North East food, drink and culture brands.", profile=dict(website="yes")),
    dict(key="tve", name="Team Valley Electrical Services Ltd", number="SYN02987", sic=["43210"], sector="Construction",
         town="Gateshead", postcode="NE11 0JQ", employees=16, incorporated="2005-11-08",
         description="Commercial and domestic electrical contractor; quotes are still built by hand in Word.", profile=dict(website="yes")),
    dict(key="sbc", name="Sunderland Bakehouse Co.", number="SYN08120", sic=["10710"], sector="Food manufacturing",
         town="Sunderland", postcode="SR1 3JD", employees=14, incorporated="2016-02-19",
         description="Craft bakery supplying cafés and delis across Wearside, plus a busy city-centre shop.", profile=dict(website="yes")),
    dict(key="wbr", name="Wearside Build & Restore Ltd", number="SYN01755", sic=["41201"], sector="Construction",
         town="Sunderland", postcode="SR5 3XB", employees=31, incorporated="2009-04-01",
         description="Refurbishment and restoration contractor for schools, churches and heritage buildings.", profile=dict(website="yes")),
    dict(key="tpf", name="Tynemouth Physio & Fitness", number="SYN09031", sic=["86900"], sector="Health & fitness",
         town="North Shields", postcode="NE29 0DL", employees=8, incorporated="2020-08-12",
         description="Physiotherapy and small-group fitness studio on the coast.", profile=dict(website="yes")),
    dict(key="ccs", name="Cathedral City Solicitors LLP", number="SYN04477", sic=["69102"], sector="Professional services",
         town="Durham", postcode="DH1 4SL", employees=12, incorporated="2012-10-03",
         description="High-street law firm: conveyancing, wills and family law.", profile=dict(website="yes")),
    dict(key="tdf", name="Tees Digital Fabrication Ltd", number="SYN07412", sic=["71129"], sector="Engineering",
         town="Middlesbrough", postcode="TS2 1RN", employees=19, incorporated="2015-07-15",
         description="3D scanning, CAD and rapid prototyping for process-industry clients on Teesside.", profile=dict(website="yes")),
    dict(key="hvf", name="Hexham Valley Farm Shop", number="SYN03958", sic=["47190"], sector="Retail",
         town="Hexham", postcode="NE46 3NH", employees=8, incorporated="2013-03-27",
         description="Farm shop and café selling Northumberland produce; wants to sell hampers online.", profile=dict(website="basic")),
    dict(key="mdw", name="Metro Data Works Ltd", number="SYN06201", sic=["62020"], sector="Technology",
         town="Newcastle upon Tyne", postcode="NE1 3DY", employees=21, incorporated="2018-12-05",
         description="Data and software consultancy helping North East SMEs and charities use their data.", profile=dict(website="yes")),
]


def _plan(weeks: int | None, steps: list[tuple[str, str]]) -> list[dict]:
    if not weeks:
        return [{"weeks": w, "focus": f, "outcome": o} for (w, (f, o)) in zip(["Month 1", "Months 2-3", "Months 4-6", "Months 7-12"], steps)]
    cuts = [0] + [round(weeks * (i + 1) / len(steps)) for i in range(len(steps))]
    span = lambda a, b: f"{a}" if a == b else f"{a}-{b}"  # noqa: E731
    return [{"weeks": span(cuts[i] + 1, cuts[i + 1]), "focus": f, "outcome": o} for i, (f, o) in enumerate(steps)]


OPPS = [
    dict(firm="tsk", title="Catering menu & pre-order form", type="paid_project", hours=12, weeks=6, rate=12.71,
         summary="Design a printable and digital catering menu for local offices, plus a simple pre-order form so the phone stops ringing at lunch.",
         tasks=["Interview the owner and 5 regular office customers", "Design the catering menu (print + PDF)", "Build a Google Form/Typeform pre-order flow", "Train staff to process orders"],
         req=["Graphic design", "Customer service", "Clear written communication"], nice=["Canva", "Figma", "Photography"],
         removed=["Design degree", "Agency experience"], measures=["Menu live by week 4", "20 pre-orders in the first fortnight"],
         q="Tell us about a time you made something easier for customers to order or understand. What did you change?",
         steps=[("Customer interviews", "Clear list of what offices want"), ("Menu design", "Approved menu"), ("Pre-order form", "Form live and tested"), ("Handover", "Staff confident using it")]),
    dict(firm="qpe", title="Digital quality records internship", type="internship", hours=30, weeks=12, rate=13.50,
         summary="Move paper job cards and inspection records into a simple digital system and build a live dashboard of late and at-risk jobs.",
         tasks=["Map the current paper process with the quality lead", "Design a digital job card (tablet friendly)", "Migrate 12 months of inspection data", "Build a late-jobs dashboard", "Train the shop floor team"],
         req=["Excel or Google Sheets", "Data cleaning", "Attention to detail"], nice=["Power BI", "Python", "SQL"],
         removed=["Engineering degree", "Manufacturing experience"], measures=["Audit prep time halved", "On-time delivery visible daily"],
         q="Describe a time you turned messy information into something people actually used. What did you do first?",
         steps=[("Shadow and map the process", "Process map signed off"), ("Design digital job card", "Pilot on one cell"), ("Migrate data and build dashboard", "Dashboard in weekly meeting"), ("Roll out and train", "All cells using it")]),
    dict(firm="wvc", title="Rota scheduling tool project", type="paid_project", hours=15, weeks=8, rate=12.71,
         summary="Replace the manual rota spreadsheet with a simple scheduling tool that matches carers to visits and flags gaps.",
         tasks=["Shadow the care coordinator for a week", "Compare 3 low-cost scheduling tools", "Configure the chosen tool and import data", "Pilot with one team and measure time saved"],
         req=["Spreadsheets", "Process mapping", "Clear communication"], nice=["Project management", "Care experience"],
         removed=["IT degree"], measures=["Rota time cut from 10 to 4 hours a week"],
         q="Tell us about a time you organised people or shifts — at work, in a club or a society. What went wrong and how did you fix it?",
         steps=[("Shadow and map", "Pain points listed"), ("Tool comparison", "Recommendation agreed"), ("Configure and import", "Tool ready"), ("Pilot", "Time saved measured")]),
    dict(firm="nla", title="Part-time bookkeeping & automation assistant", type="part_time", hours=15, weeks=16, rate=13.00,
         summary="Help with client bookkeeping in Xero and automate repetitive reconciliation tasks.",
         tasks=["Process receipts and bank feeds in Xero", "Build templates for monthly client packs", "Automate a reconciliation check in Excel"],
         req=["Excel", "Attention to detail", "Numeracy"], nice=["Xero", "Bookkeeping"], removed=["Accounting degree", "AAT qualification"],
         measures=["Month-end packs out 2 days faster"], q="What's the most fiddly spreadsheet or numbers task you've done, and how did you make sure it was right?",
         steps=[("Xero training", "Processing independently"), ("Templates", "Client pack template live"), ("Automation", "Reconciliation check in use")]),
    dict(firm="ocs", title="Junior content & social media assistant", type="part_time", hours=12, weeks=12, rate=12.71,
         summary="Create short-form video and social posts for North East food and culture clients.",
         tasks=["Shoot and edit short videos", "Write captions", "Schedule posts and report results"],
         req=["Social media", "Video editing", "Copywriting"], nice=["Canva", "Photography"], removed=["Marketing degree"],
         measures=["3 client accounts supported"], q="Share a post or video you made that people engaged with. Why do you think it worked?",
         steps=[("Onboarding", "Brand guides learned"), ("Content production", "Weekly content shipped"), ("Reporting", "Monthly report delivered")]),
    dict(firm="tve", title="Digital quoting tool project", type="paid_project", hours=15, weeks=8, rate=13.00,
         summary="Turn hand-written Word quotes into a spreadsheet-based quoting tool with a price list and PDF output.",
         tasks=["Collect 20 past quotes", "Build a structured price list", "Create the quoting template", "Train the office manager"],
         req=["Excel", "Process mapping"], nice=["Python", "Construction knowledge"], removed=["Electrical qualification"],
         measures=["Quote time cut from 2 hours to 30 minutes"], q="Describe something repetitive you automated or simplified. What was the result?",
         steps=[("Collect and analyse", "Price list drafted"), ("Build tool", "Template working"), ("Pilot", "10 live quotes produced"), ("Handover", "Office manager independent")]),
    dict(firm="sbc", title="E-commerce & wholesale orders internship", type="internship", hours=25, weeks=12, rate=12.71,
         summary="Launch online ordering for wholesale café customers and improve the bakery's Shopify shop.",
         tasks=["Set up a wholesale ordering portal", "Photograph and list products", "Create a weekly order report"],
         req=["Shopify or a website builder", "Customer service"], nice=["Photography", "SEO", "Excel"], removed=["Business degree"],
         measures=["50% of wholesale orders online by week 12"], q="If you were a café owner ordering bread every week, what would make ordering online easier than a phone call?",
         steps=[("Customer research", "Wholesale needs mapped"), ("Portal setup", "Portal live"), ("Product content", "All products listed"), ("Reporting", "Weekly report automated")]),
    dict(firm="wbr", title="Assistant project coordinator", type="first_job", hours=37, weeks=None, rate=13.40,
         summary="Entry-level role supporting site managers with schedules, supplier orders and client updates on heritage projects.",
         tasks=["Maintain project schedules", "Order materials and track deliveries", "Write weekly client updates", "Support health & safety paperwork"],
         req=["Organisation", "Excel", "Clear written communication"], nice=["Project management", "CSCS card"], removed=["Construction management degree", "2 years' experience"],
         measures=["Owns schedules for 3 projects by month 6"], q="Tell us about a project with lots of moving parts that you kept on track. How?",
         steps=[("Induction and shadowing", "Knows the systems"), ("Supporting 2 projects", "Owns supplier orders"), ("Coordinating", "Owns schedules"), ("Progression review", "Path to project manager agreed")]),
    dict(firm="tpf", title="Online booking & member comms project", type="paid_project", hours=10, weeks=6, rate=12.71,
         summary="Move class bookings online and set up automated reminder emails to cut no-shows.",
         tasks=["Compare booking tools", "Set up classes and payments", "Write reminder email sequence"],
         req=["Website builder", "Customer service"], nice=["Email marketing", "Fitness interest"], removed=["Sports science degree"],
         measures=["No-shows down 30%"], q="What would make you more likely to turn up to a class you'd booked?",
         steps=[("Tool choice", "Tool selected"), ("Setup", "Bookings live"), ("Comms", "Reminders running")]),
    dict(firm="ccs", title="Client intake process mapping", type="paid_project", hours=12, weeks=6, rate=12.71,
         summary="Map how new clients are onboarded and design a simpler online intake form.",
         tasks=["Interview staff", "Map the intake journey", "Design an online intake form"],
         req=["Process mapping", "Clear written communication"], nice=["Law interest", "UX research"], removed=["Law degree"],
         measures=["Intake time halved"], q="Describe a form or process that frustrated you. How would you redesign it?",
         steps=[("Interviews", "Journey mapped"), ("Design", "Form prototype"), ("Pilot", "Form in use")]),
    dict(firm="tdf", title="CAD & 3D scanning internship", type="internship", hours=30, weeks=12, rate=13.20,
         summary="Support engineers with 3D scanning, CAD clean-up and documentation for industrial clients.",
         tasks=["Process 3D scan data", "Clean up CAD models", "Write technical reports"],
         req=["CAD", "Attention to detail"], nice=["SolidWorks", "Python"], removed=["Chartered status"],
         measures=["Owns scan-to-CAD for 2 client jobs"], q="Tell us about a technical drawing, model or design project you're proud of.",
         steps=[("Training", "Safe on equipment"), ("Supported jobs", "First models delivered"), ("Independent jobs", "Two client jobs owned")]),
    dict(firm="hvf", title="Online hamper shop build", type="paid_project", hours=12, weeks=8, rate=12.71,
         summary="Build an online shop for Northumberland produce hampers with local delivery and click-and-collect.",
         tasks=["Photograph products", "Set up Shopify/Squarespace shop", "Configure delivery zones"],
         req=["Website builder", "Photography"], nice=["Copywriting", "SEO"], removed=["E-commerce experience"],
         measures=["Shop live before December"], q="Show us a product photo you've taken and tell us how you'd sell it online.",
         steps=[("Content", "Photos and copy ready"), ("Build", "Shop built"), ("Launch", "First orders")]),
    dict(firm="mdw", title="Junior data analyst", type="first_job", hours=37, weeks=None, rate=14.40,
         summary="Graduate role building dashboards and data pipelines for North East SMEs and charities.",
         tasks=["Clean and model client data", "Build Power BI dashboards", "Present findings to clients"],
         req=["SQL", "Data analysis", "Python"], nice=["Power BI", "Statistics"], removed=["Master's degree", "Commercial experience"],
         measures=["Delivers first client dashboard by month 3"], q="Walk us through a data project you've done — what question did it answer?",
         steps=[("Onboarding", "Tooling set up"), ("Shadowing client work", "First pipeline"), ("Own small projects", "First dashboard delivered"), ("Review", "Path to analyst II agreed")]),
]

STUDENTS = [
    dict(user="aisha.rahman@student.example", name="Aisha Rahman", email="aisha.rahman@student.example", phone="07700 900123",
         headline="Computer Science graduate who loves building things people actually use", degree="BSc Computer Science",
         university="Newcastle University", year=2026, town="Gateshead", travel=12, hours=20, visa=True,
         availability="Weekdays; café shifts Sat-Sun", skills=["Python", "SQL", "React", "HTML", "CSS", "Figma", "Data analysis", "Customer service", "Cash handling"],
         exp=[dict(title="Barista & shift lead", organisation="Quayside coffee shop", period="2023-2026", summary="Ran weekend shifts, trained new staff and handled 300+ customers a day."),
              dict(title="Final-year project", organisation="Newcastle University", period="2025-2026", summary="Built a React + Flask app that predicts Metro delays from open data.")],
         interests=["Technology", "Food & hospitality", "Data"]),
    dict(user="tom.hughes@student.example", name="Tom Hughes", email="tom.hughes@student.example", phone="07700 900456",
         headline="Marketing graduate with a knack for short-form video", degree="BA Business & Marketing",
         university="Northumbria University", year=2025, town="Sunderland", travel=15, hours=25, visa=False,
         availability="Flexible, mornings preferred", skills=["Social media", "Canva", "Video editing", "Copywriting", "Excel", "Sales", "Photography"],
         exp=[dict(title="Sales assistant", organisation="City-centre sports retailer", period="2022-2025", summary="Top seller for 3 quarters; ran the store's Instagram."),
              dict(title="Society social media lead", organisation="Northumbria Students' Union", period="2023-2024", summary="Grew followers from 800 to 4,000.")],
         interests=["Creative & marketing", "Food", "Retail"]),
    dict(user="priya.nair@student.example", name="Priya Nair", email="priya.nair@student.example", phone="07700 900789",
         headline="Mechanical engineer interested in digital manufacturing", degree="MEng Mechanical Engineering",
         university="Durham University", year=2026, town="Durham", travel=25, hours=37, visa=False,
         availability="Full-time from July", skills=["CAD", "SolidWorks", "MATLAB", "Python", "Excel", "Report writing", "Data analysis"],
         exp=[dict(title="Summer placement", organisation="Automotive supplier (Washington)", period="2025", summary="Analysed scrap data and proposed a fixture change that cut rework."),
              dict(title="Tutor", organisation="Online maths tutoring", period="2023-2026", summary="Tutored GCSE maths students weekly.")],
         interests=["Manufacturing", "Engineering", "Data"]),
    # Synthetic applicants without logins (they apply to the owners' roles)
    dict(name="Liam Carter", email="liam.carter@student.example", headline="Design graduate", degree="BA Graphic Design", university="University of Sunderland",
         year=2026, town="Gateshead", travel=10, hours=15, visa=False, availability="Afternoons",
         skills=["Graphic design", "Canva", "Figma", "Photography", "Customer service"],
         exp=[dict(title="Waiter", organisation="Italian restaurant", period="2022-2026", summary="Front-of-house in a busy restaurant; designed their specials boards.")], interests=["Food"]),
    dict(name="Chen Wei", email="chen.wei@student.example", headline="Data science MSc", degree="MSc Data Science", university="Newcastle University",
         year=2026, town="Newcastle upon Tyne", travel=15, hours=20, visa=True, availability="Mon-Thu",
         skills=["Python", "SQL", "Power BI", "Statistics", "Excel", "Data cleaning"],
         exp=[dict(title="Research assistant", organisation="University lab", period="2025-2026", summary="Cleaned and analysed sensor datasets.")], interests=["Data", "Manufacturing"]),
    dict(name="Grace Thompson", email="grace.thompson@student.example", headline="Psychology graduate and care worker", degree="BSc Psychology", university="Durham University",
         year=2025, town="Chester-le-Street", travel=15, hours=20, visa=False, availability="Weekdays",
         skills=["Scheduling", "Excel", "Customer service", "Report writing"],
         exp=[dict(title="Care assistant", organisation="Residential care home", period="2021-2025", summary="Supported residents and helped the manager with rota swaps.")], interests=["Care"]),
    dict(name="Omar Haddad", email="omar.haddad@student.example", headline="Business analytics graduate", degree="BSc Business Analytics", university="Northumbria University",
         year=2026, town="Gateshead", travel=10, hours=30, visa=False, availability="Full-time",
         skills=["Excel", "Power BI", "Data analysis", "Process mapping"],
         exp=[dict(title="Warehouse operative", organisation="Distribution centre", period="2022-2025", summary="Night shifts; suggested a picking layout change.")], interests=["Manufacturing", "Logistics"]),
    dict(name="Sophie Bell", email="sophie.bell@student.example", headline="Marketing & events", degree="BA Marketing", university="University of Sunderland",
         year=2026, town="Sunderland", travel=12, hours=12, visa=False, availability="Evenings",
         skills=["Social media", "Event planning", "Copywriting", "Customer service"],
         exp=[dict(title="Bar staff", organisation="Live music venue", period="2023-2026", summary="Handled busy nights and ran the venue's event listings.")], interests=["Food", "Events"]),
]

APPLICATIONS = [
    # (student email, firm key, opp title, status, days ago, answer)
    ("aisha.rahman@student.example", "mdw", "Junior data analyst", "interview", 12,
     "For my final-year project I combined Nexus Metro open data with weather data to predict delays. I cleaned two years of records in Python, modelled them in SQL and built a React dashboard my classmates used to plan journeys."),
    ("aisha.rahman@student.example", "qpe", "Digital quality records internship", "submitted", 3,
     "At the café our stock counts lived on paper and we kept running out of oat milk. I moved them into a shared Google Sheet with a simple reorder alert, which the manager still uses every week."),
    ("liam.carter@student.example", "tsk", "Catering menu & pre-order form", "submitted", 4,
     "I redesigned the specials board at the restaurant where I work so the dishes were grouped by price and dietary needs. Orders for the specials went up and staff stopped answering the same questions all night."),
    ("sophie.bell@student.example", "tsk", "Catering menu & pre-order form", "submitted", 2,
     "I run the event listings for a music venue. I switched our ticket info from a long Facebook post to a simple one-page listing with a booking link, and fewer people messaged us asking for prices."),
    ("chen.wei@student.example", "qpe", "Digital quality records internship", "shortlisted", 6,
     "In the lab I inherited sensor data from five different spreadsheets with different date formats. I wrote a Python script to standardise them, flagged missing readings, and built one clean dataset the team now uses."),
    ("omar.haddad@student.example", "qpe", "Digital quality records internship", "submitted", 1,
     "On night shifts our picking errors were logged on paper and nobody looked at them. I started a simple tally in Excel by aisle, which showed one badly labelled aisle caused most errors — it was relabelled the next week."),
    ("grace.thompson@student.example", "wvc", "Rota scheduling tool project", "submitted", 5,
     "At the care home I helped the manager handle shift swaps. We kept a swap log in Excel and a WhatsApp group, which stopped double-bookings but was still messy. I'd love to help build something better."),
]

# 12 months of synthetic metrics. Implemented suggestions create a visible uplift.
METRICS = {
    "tsk": dict(base=21000, customers=2600, growth=0.004, uplifts={"2026-05": 0.12}),
    "qpe": dict(base=142000, customers=38, growth=0.003, uplifts={"2026-04": 0.07}),
    "wvc": dict(base=96000, customers=210, growth=0.002, uplifts={"2026-03": 0.05}),
}
IMPLEMENTED = {
    "tsk": dict(category="digital", title="Set up a Google Business Profile and card payments", month="2026-05",
                problem="Customers couldn't find opening hours and some walked away when it was cash only.",
                recommendation="Claim the Google profile, add photos and hours, accept contactless.",
                impact="More walk-ins from Google Maps and bigger average spend.", effort="low", evidence="640 reviews but no listed hours."),
    "qpe": dict(category="operations", title="Pilot digital job cards on one machining cell", month="2026-04",
                problem="Paper job cards hid which jobs were running late.", recommendation="Pilot tablet job cards on Cell 2.",
                impact="Earlier warning on late jobs.", effort="medium", evidence="On-time delivery 84%."),
    "wvc": dict(category="people", title="Publish an online recruitment page", month="2026-03",
                problem="Recruiting relied on word of mouth.", recommendation="Simple careers page with an application form.",
                impact="More applicants for carer roles.", effort="low", evidence="Turnover 31%."),
}


def _months(n: int) -> list[str]:
    today = date.today().replace(day=1)
    out = []
    for i in range(n, 0, -1):
        y, m = today.year, today.month - i
        while m <= 0:
            m += 12
            y -= 1
        out.append(f"{y:04d}-{m:02d}")
    return out


def seed() -> None:
    random.seed(42)
    passwords = _load_or_create_passwords()
    if settings.db_path.exists():
        settings.db_path.unlink()
        for suffix in ("-wal", "-shm"):
            p = settings.db_path.with_name(settings.db_path.name + suffix)
            if p.exists():
                p.unlink()
    init_db()
    conn = connect()
    with conn:
        user_ids = {}
        for email, role, name in USERS:
            cur = conn.execute("INSERT INTO users (email, password_hash, role, display_name) VALUES (?, ?, ?, ?)",
                               (email, hash_password(passwords[email]), role, name))
            user_ids[email] = cur.lastrowid

        firm_ids = {}
        for f in FIRMS:
            cur = conn.execute(
                """INSERT INTO firms (owner_user_id, name, company_number, sic_codes, sector, town, postcode, employees, incorporated, description, profile)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_ids.get(f.get("owner")), f["name"], f["number"], dumps(f["sic"]), f["sector"], f["town"], f["postcode"],
                 f["employees"], f["incorporated"], f["description"], dumps(f["profile"])),
            )
            firm_ids[f["key"]] = cur.lastrowid

        opp_ids = {}
        now = datetime.utcnow()
        for i, o in enumerate(OPPS):
            created = (now - timedelta(days=20 - i)).strftime("%Y-%m-%d %H:%M:%S")
            cur = conn.execute(
                """INSERT INTO opportunities (firm_id, title, type, summary, tasks, plan, skills_required, skills_nice, removed_requirements,
                       success_measures, hours_per_week, weeks, hourly_rate, role_question, ai_reasoning, visibility, status, source, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'internal', 'published', 'seed', ?)""",
                (firm_ids[o["firm"]], o["title"], o["type"], o["summary"], dumps(o["tasks"]), dumps(_plan(o["weeks"], o["steps"])),
                 dumps(o["req"]), dumps(o["nice"]), dumps(o["removed"]), dumps(o["measures"]), o["hours"], o["weeks"], o["rate"], o["q"],
                 "Scoped with the FirstHire Growth Advisor and approved by the firm.", created),
            )
            opp_ids[(o["firm"], o["title"])] = cur.lastrowid

        student_ids = {}
        for s in STUDENTS:
            cur = conn.execute(
                """INSERT INTO students (user_id, full_name, email, phone, headline, degree, university, grad_year, home_town,
                       max_travel_miles, hours_per_week, availability, on_student_visa, skills, experiences, interests, consent_ai)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                (user_ids.get(s.get("user")), s["name"], s["email"], s.get("phone", ""), s["headline"], s["degree"], s["university"],
                 s["year"], s["town"], s["travel"], s["hours"], s["availability"], int(s["visa"]), dumps(s["skills"]),
                 dumps(s["exp"]), dumps(s["interests"])),
            )
            student_ids[s["email"]] = cur.lastrowid

        flow = ["submitted", "shortlisted", "interview"]
        notes = {"submitted": "Application sent. The firm sees your answer and skills first — not your name or university.",
                 "shortlisted": "Shortlisted — the firm liked your answer and wants a closer look.",
                 "interview": "Invited to interview. The firm can now see your name and contact details. Proposed time: Thursday 10:00 at their Newcastle office."}
        for email, fkey, title, status, days, answer in APPLICATIONS:
            created = now - timedelta(days=days)
            cur = conn.execute(
                "INSERT INTO applications (opportunity_id, student_id, answer, status, created_at, updated_at, interview_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (opp_ids[(fkey, title)], student_ids[email], answer, status, created.strftime("%Y-%m-%d %H:%M:%S"),
                 now.strftime("%Y-%m-%d %H:%M:%S"), "Thursday 10:00" if status == "interview" else None),
            )
            for step_i, step in enumerate(flow[: flow.index(status) + 1]):
                conn.execute("INSERT INTO application_events (application_id, status, note, created_at) VALUES (?, ?, ?, ?)",
                             (cur.lastrowid, step, notes[step], (created + timedelta(days=step_i * 2)).strftime("%Y-%m-%d %H:%M:%S")))
            uid = user_ids.get(email)
            if uid and status == "interview":
                conn.execute("INSERT INTO access_log (subject_user_id, actor, action, detail, created_at) VALUES (?, ?, ?, ?, ?)",
                             (uid, "Metro Data Works Ltd", "Name and contact details revealed", "Because they invited you to interview",
                              (created + timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S")))

        months = _months(12)
        for key, m in METRICS.items():
            level = 1.0
            for month in months:
                level *= 1 + m["growth"] + random.uniform(-0.025, 0.025)
                if month in m["uplifts"]:
                    level *= 1 + m["uplifts"][month]
                seasonal = 1 + 0.06 * (1 if month[5:] in {"07", "08", "12"} else 0) - 0.04 * (1 if month[5:] in {"01", "02"} else 0)
                conn.execute("INSERT INTO firm_metrics (firm_id, month, revenue, customers) VALUES (?, ?, ?, ?)",
                             (firm_ids[key], month, round(m["base"] * level * seasonal, 2), round(m["customers"] * level * seasonal)))
            # Fix uplift months so they fall inside the 12-month window for the chart
            imp = IMPLEMENTED[key]
            imp_month = imp["month"] if imp["month"] in months else months[len(months) // 2]
            conn.execute(
                """INSERT INTO insights (firm_id, category, title, problem, recommendation, expected_impact, effort, evidence,
                       opportunity_type, role_title, status, source, implemented_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'none', '', 'implemented', 'seed', ?)""",
                (firm_ids[key], imp["category"], imp["title"], imp["problem"], imp["recommendation"], imp["impact"],
                 imp["effort"], imp["evidence"], imp_month),
            )

        # Pre-generate offline insights so the owner dashboard is never empty
        from .ai import heuristics
        from .ai.owner_agent import firm_context

        for key in METRICS:
            firm = conn.execute("SELECT * FROM firms WHERE id = ?", (firm_ids[key],)).fetchone()
            for i in heuristics.insights(firm_context(conn, firm)):
                conn.execute(
                    """INSERT INTO insights (firm_id, category, title, problem, recommendation, expected_impact, effort, evidence,
                           opportunity_type, role_title, status, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', 'offline')""",
                    (firm_ids[key], i.category, i.title, i.problem, i.recommendation, i.expected_impact, i.effort, i.evidence,
                     i.opportunity_type, i.role_title),
                )
    conn.close()
    print(f"Seeded {len(FIRMS)} firms, {len(OPPS)} opportunities, {len(STUDENTS)} graduates, {len(USERS)} demo logins.")
    print(f"Demo credentials written to {CRED_FILE} (git-ignored).")


if __name__ == "__main__":
    seed()
