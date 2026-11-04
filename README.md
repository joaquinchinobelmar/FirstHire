# FirstHire (working name)

Local-first jobs for North East graduates. Small firms describe a real business problem, an AI
Growth Advisor turns it into a fair, paid opportunity, and an AI matcher shows it to local graduates
with a clear "why it fits". People make every hiring decision.

> Hackathon prototype. **All firms, people and numbers are synthetic.**

## Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React 19 + Vite + TypeScript + Tailwind v4, Recharts, lucide icons | Fast to build, easy to wrap as a mobile app later (Capacitor / React Native port) |
| Backend | Python FastAPI + SQLite | Zero-setup DB, matches the team's existing Python + `anthropic` skeleton |
| AI | Anthropic Claude (`claude-opus-5-5`) with structured outputs | Typed JSON responses; a rule-based offline engine takes over if there's no key or a call fails |
| Registry data | Companies House Public Data API (optional free key) | Verifies firms and builds outreach lists by SIC code + location; a synthetic snapshot is used otherwise |

## Run it locally

Prerequisites: Python 3.11+, Node 20+.

```bash
# 1) Backend  (terminal 1)
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # optional: add ANTHROPIC_API_KEY / COMPANIES_HOUSE_API_KEY
python -m app.seed                # creates the synthetic demo data + demo logins
uvicorn app.main:app --reload --port 8000

# 2) Frontend (terminal 2)
cd frontend
npm install
npm run dev                       # http://localhost:5173  (proxies /api to :8000)
```

**Demo logins:** `python -m app.seed` writes them to `backend/DEMO_CREDENTIALS.local.md`.
That file is git-ignored and the passwords exist only there (as plain text) and as salted hashes in
the DB. They are never sent to the frontend. Re-running the seed resets the demo data and keeps
the same passwords.

API docs: http://localhost:8000/api/docs · Health/AI mode: http://localhost:8000/api/health

### Modes

- **Claude mode:** set `ANTHROPIC_API_KEY` in `backend/.env`. The UI shows a "Claude AI" badge.
- **Offline demo mode:** no key, or `AI_MODE=offline`. Deterministic rule-based agents with the same
  output shapes, so the demo never breaks on stage.
- **Companies House live:** set `COMPANIES_HOUSE_API_KEY` (free at developer.company-information.service.gov.uk).
  Synthetic firms (company numbers starting `SYN`) always use the local snapshot.

## What's in the prototype

**Graduate**
1. *My Passport*: CV upload (PDF/txt) → AI draft of skills & experience → you review and save. Travel
   radius, hours, Student-visa flag, AI-matching consent, and a live "What the AI sees" preview.
2. *Opportunities*: code filters to roles inside the North East, within your radius and hour limit;
   Claude scores fit and explains it (reasons, skill gaps, transferable part-time experience, local career
   path). Swipe-style "Discover" view (← / → keys) or a grid. Apply with one role-specific answer and a
   monthly limit (8).
3. *Applications*: status stepper, timeline, messages from the firm, withdraw.

**Business owner**
1. *Growth Advisor*: KPIs, revenue/customer trend with markers where AI suggestions went live and a
   code-calculated before/after uplift; proactive insights ("640 reviews but no website"); a prompt box
   that returns suggestions plus a draft opportunity (type, tasks, plan, skills, removed requirements,
   role question). Code sets pay ≥ National Living Wage, caps hours and calculates the full cost before
   the owner publishes it as an **internal** opportunity.
2. *Applicants*: blind first review (no name, university or contact details) in order of application,
   with no AI ranking. Shortlist → invite to interview (reveals identity and logs it for the graduate) → offer / reject with
   a kind message.

**Trust & privacy** (`/trust`): data-use promises, per-user access log, JSON export, account deletion.
Security: PBKDF2 password hashes, random session tokens stored hashed, HttpOnly SameSite cookies,
login rate limiting, security headers, PII redaction before any AI call, prompt-injection-aware prompts.

## Project layout

```
backend/app/
  main.py              FastAPI app, health, public stats, Companies House search
  config.py db.py      settings, SQLite schema
  security.py          hashing, sessions, role guards, rate limit
  wages.py geo.py      pay rules (NLW Apr 2026) and North East geography
  companies_house.py   Companies House API client + synthetic snapshot
  seed.py              synthetic data + demo credentials
  ai/                  client.py (Claude wrapper), student_agent.py, owner_agent.py,
                       heuristics.py (offline engine), privacy.py (redaction), schemas.py
  routers/             auth, student, owner, account
frontend/src/
  pages/               Landing, Login, Trust, graduate/*, owner/*
  components/          UI kit, AppShell, ImpactChart, OpportunityEditor
```
