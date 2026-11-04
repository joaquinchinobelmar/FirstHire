"""Pay rules. Code — never the model — calculates pay and checks fixed rules.

Rates are the April 2026 UK statutory minimums. Verify before any real launch.
FirstHire rule: every opportunity pays at least the 21+ National Living Wage,
whatever the student's age and whatever the role is called. No unpaid work.
"""

NLW_APRIL_2026 = 12.71          # 21 and over
RATE_18_20_APRIL_2026 = 10.85
HOLIDAY_ACCRUAL = 0.1207        # 5.6 weeks' statutory leave for irregular-hours workers
STUDENT_VISA_TERM_HOURS = 20
FULL_TIME_HOURS = 37.5

TYPE_LABELS = {
    "paid_project": "Paid project",
    "part_time": "Part-time role",
    "internship": "Internship",
    "first_job": "First job",
}


def default_weeks(opportunity_type: str) -> int | None:
    return {"paid_project": 8, "part_time": 12, "internship": 12, "first_job": None}.get(opportunity_type, 12)


def cost_breakdown(hourly_rate: float, hours_per_week: float, weeks: int | None, opportunity_type: str) -> dict:
    rate = round(max(hourly_rate, 0), 2)
    if opportunity_type == "first_job" or not weeks:
        annual = round(rate * hours_per_week * 52.14, 2)
        return {
            "kind": "salary",
            "hourly_rate": rate,
            "annual_salary": annual,
            "monthly_salary": round(annual / 12, 2),
            "meets_minimum": rate >= NLW_APRIL_2026,
            "minimum_rate": NLW_APRIL_2026,
            "visa_friendly": hours_per_week <= STUDENT_VISA_TERM_HOURS,
            "notes": "Salary before employer NI and pension. First-year progression should be stated in the advert.",
        }
    wages = round(rate * hours_per_week * weeks, 2)
    holiday = round(wages * HOLIDAY_ACCRUAL, 2)
    return {
        "kind": "fixed_term",
        "hourly_rate": rate,
        "weeks": weeks,
        "hours_per_week": hours_per_week,
        "wages": wages,
        "holiday_accrual": holiday,
        "total_estimate": round(wages + holiday, 2),
        "meets_minimum": rate >= NLW_APRIL_2026,
        "minimum_rate": NLW_APRIL_2026,
        "visa_friendly": hours_per_week <= STUDENT_VISA_TERM_HOURS,
        "notes": "Estimate before employer NI/pension. Holiday accrual at 12.07%. Actual rates depend on age and the role.",
    }


def validate_opportunity(opportunity_type: str, hourly_rate: float, hours_per_week: int, weeks: int | None) -> list[str]:
    """Hard rules. Returns a list of human-readable problems (empty = OK)."""
    problems = []
    if opportunity_type not in TYPE_LABELS:
        problems.append("Unknown opportunity type.")
    if hourly_rate < NLW_APRIL_2026:
        problems.append(f"Pay must be at least £{NLW_APRIL_2026:.2f}/hour (National Living Wage). FirstHire never publishes unpaid or underpaid work.")
    if hours_per_week < 4 or hours_per_week > 48:
        problems.append("Hours per week must be between 4 and 48.")
    if opportunity_type in {"paid_project", "part_time"} and hours_per_week > STUDENT_VISA_TERM_HOURS:
        problems.append(f"Paid projects and part-time roles are capped at {STUDENT_VISA_TERM_HOURS} h/week so they fit around study and Student-visa limits.")
    if opportunity_type != "first_job" and (not weeks or weeks < 2 or weeks > 52):
        problems.append("Fixed-term opportunities need a duration between 2 and 52 weeks.")
    return problems
