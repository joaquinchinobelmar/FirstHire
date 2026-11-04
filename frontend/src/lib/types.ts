export type Role = "graduate" | "owner";
export type User = { id: number; name: string; role: Role; email: string };

export type OppType = "paid_project" | "part_time" | "internship" | "first_job";

export type PlanStep = { weeks: string; focus: string; outcome: string };

export type Cost = {
  kind: "fixed_term" | "salary";
  hourly_rate: number;
  weeks?: number;
  hours_per_week?: number;
  wages?: number;
  holiday_accrual?: number;
  platform_fee: number;
  total_estimate?: number;
  annual_salary?: number;
  monthly_salary?: number;
  meets_minimum: boolean;
  minimum_rate: number;
  visa_friendly: boolean;
  notes: string;
};

export type Opportunity = {
  id: number;
  title: string;
  type: OppType;
  type_label: string;
  summary: string;
  tasks: string[];
  plan: PlanStep[];
  skills_required: string[];
  skills_nice: string[];
  removed_requirements: string[];
  success_measures: string[];
  hours_per_week: number;
  weeks: number | null;
  hourly_rate: number;
  cost: Cost;
  role_question: string;
  ai_reasoning: string;
  remote_friendly: boolean;
  visibility: string;
  status: string;
  source: string;
  insight_id: number | null;
  created_at: string;
  distance_miles: number | null;
  firm: { id: number; name: string; sector: string; town: string; employees: number; description: string };
  applicant_counts?: Record<string, number>;
  applicant_total?: number;
};

export type MatchInfo = {
  opportunity_id: number;
  fit_score: number;
  headline: string;
  reasons: string[];
  skill_gaps: string[];
  transferable_experience: string;
  career_path: string;
};

export type MatchedOpportunity = Opportunity & { match: MatchInfo };

export type MatchesResponse = {
  source: "claude" | "offline";
  note: string | null;
  profile_summary: string;
  strengths: string[];
  matches: MatchedOpportunity[];
  filtered: { outside_radius: number; outside_region: number; over_hour_limit: number; radius_miles: number; home_town: string };
  applications_this_month: number;
  monthly_limit: number;
};

export type Experience = { title: string; organisation: string; period: string; summary: string };

export type Passport = {
  full_name: string;
  email: string;
  phone: string;
  headline: string;
  degree: string;
  university: string;
  grad_year: number | null;
  home_town: string;
  max_travel_miles: number;
  hours_per_week: number;
  availability: string;
  on_student_visa: boolean;
  consent_ai: boolean;
  skills: string[];
  experiences: Experience[];
  interests: string[];
  cv_text: string;
  updated_at: string;
  ai_preview: Record<string, unknown>;
  towns: string[];
};

export type CvDraft = {
  source: "claude" | "offline";
  headline: string;
  summary: string;
  skills: string[];
  experiences: Experience[];
  interests: string[];
};

export type AppEvent = { status: string; note: string; created_at: string };
export type StudentApplication = {
  id: number;
  status: string;
  answer: string;
  owner_note: string;
  interview_at: string | null;
  created_at: string;
  updated_at: string;
  opportunity: Opportunity;
  events: AppEvent[];
};

export type Insight = {
  id: number;
  category: string;
  title: string;
  problem: string;
  recommendation: string;
  expected_impact: string;
  effort: "low" | "medium" | "high";
  evidence: string;
  opportunity_type: OppType | "none";
  role_title: string;
  status: "new" | "accepted" | "dismissed" | "implemented";
  source: string;
  opportunity_id: number | null;
  implemented_at: string | null;
};

export type Impact = {
  insight_id: number;
  title: string;
  month: string;
  revenue_before: number;
  revenue_after: number;
  revenue_change_pct: number;
  customers_before: number;
  customers_after: number;
  customers_change_pct: number;
};

export type Dashboard = {
  firm: {
    id: number; name: string; company_number: string; sector: string; town: string; postcode: string;
    employees: number; incorporated: string; description: string; sic_codes: string[]; profile: Record<string, unknown>;
  };
  companies_house: Record<string, any> | null;
  companies_house_mode: "live" | "snapshot";
  metrics: { month: string; revenue: number; customers: number }[];
  impact: Impact[];
  kpis: null | {
    month: string; revenue: number; customers: number; revenue_vs_prev3_pct: number;
    implemented_count: number; open_roles: number; new_applicants: number;
  };
  insights: Insight[];
  opportunities: Opportunity[];
  ai_mode: "claude" | "offline";
  rules: { minimum_rate: number; max_part_time_hours: number; platform_fee_monthly: number };
};

export type DraftOpportunity = {
  title: string;
  type: OppType;
  type_label: string;
  summary: string;
  tasks: string[];
  plan: PlanStep[];
  skills_required: string[];
  skills_nice: string[];
  removed_requirements: string[];
  success_measures: string[];
  hours_per_week: number;
  weeks: number | null;
  hourly_rate: number;
  role_question: string;
  reasoning: string;
  cost: Cost;
};

export type AdvisorResult = {
  source: "claude" | "offline";
  understanding: string;
  suggestions: { title: string; recommendation: string; why: string; effort: string }[];
  needs_hire: boolean;
  opportunity: DraftOpportunity;
  insight_id?: number;
};

export type Applicant = {
  id: number;
  code: string;
  status: string;
  answer: string;
  owner_note: string;
  interview_at: string | null;
  created_at: string;
  opportunity: { id: number; title: string; type: OppType; role_question: string };
  evidence: {
    degree_subject: string;
    graduation_year: number | null;
    skills: string[];
    skills_matching_role: string[];
    experiences: { title: string; period: string; summary: string }[];
    hours_available: number;
    availability: string;
    distance_miles: number | null;
    term_time_limit: number | null;
  };
  identity: null | { name: string; email: string; phone: string; university: string };
};
