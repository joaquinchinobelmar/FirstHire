"""Structured-output schemas. Claude must answer in exactly these shapes."""

from typing import Literal

from pydantic import BaseModel

OpportunityType = Literal["paid_project", "part_time", "internship", "first_job"]
Effort = Literal["low", "medium", "high"]


# ---------- Agent 1: graduate matching ----------
class Experience(BaseModel):
    title: str
    organisation: str
    period: str
    summary: str


class CVProfile(BaseModel):
    headline: str
    summary: str
    skills: list[str]
    experiences: list[Experience]
    interests: list[str]


class Match(BaseModel):
    opportunity_id: int
    fit_score: int
    headline: str
    reasons: list[str]
    skill_gaps: list[str]
    transferable_experience: str
    career_path: str


class MatchResult(BaseModel):
    profile_summary: str
    strengths: list[str]
    matches: list[Match]


# ---------- Agent 2: business growth advisor ----------
class Insight(BaseModel):
    category: Literal["digital", "marketing", "operations", "data", "people", "finance"]
    title: str
    problem: str
    recommendation: str
    expected_impact: str
    effort: Effort
    evidence: str
    opportunity_type: Literal["paid_project", "part_time", "internship", "first_job", "none"]
    role_title: str


class InsightList(BaseModel):
    insights: list[Insight]


class PlanStep(BaseModel):
    weeks: str
    focus: str
    outcome: str


class OpportunityDraft(BaseModel):
    title: str
    type: OpportunityType
    summary: str
    tasks: list[str]
    plan: list[PlanStep]
    skills_required: list[str]
    skills_nice: list[str]
    removed_requirements: list[str]
    success_measures: list[str]
    hours_per_week: int
    weeks: int
    role_question: str
    reasoning: str


class Suggestion(BaseModel):
    title: str
    recommendation: str
    why: str
    effort: Effort


class AdvisorResult(BaseModel):
    understanding: str
    suggestions: list[Suggestion]
    needs_hire: bool
    opportunity: OpportunityDraft
