# ARS Engine — Acquisition Readiness Score Intelligence Platform

> **Transform raw lead lists into ranked acquisition targets using AI-powered signal analysis.**
> Built for ETA searchers and lower-middle-market PE operators who need to know *which* companies are ready to be acquired — not just which ones exist.

---
Live Demo
---

> 🔗 **[Try ARS Engine →](https://aquamarine-valkyrie-50a6ed.netlify.app)**
> 📹 **[2-Minute Video Walkthrough →]([https://loom.com/your-link](https://www.loom.com/share/541ef5c8772e4b7e9428ab537e73a735))**

## What It Does

SaaSquatch and Apollo give you a list. ARS Engine tells you who to call first.

Upload any CSV of companies. Every company gets scored 0–100 across five acquisition-readiness dimensions, ranked by tier, and enriched with an AI-written acquisition thesis, risk flag, and a personalized outreach email — all ready to send.

**The five scoring dimensions:**

| Dimension | Weight | What it measures |
|---|---|---|
| Owner Exit Signal | 30% | Founder age, succession hiring, COO postings, business tenure |
| Financial Health | 25% | Revenue trajectory, growth signals, funding history |
| Operational Leverage | 20% | Team depth, tech stack maturity, systematization signals |
| Market Tailwinds | 15% | Industry growth/contraction context |
| Competitive Moat | 10% | Niche positioning, proprietary assets, category dominance |

Owner exit signals are weighted highest because in ETA, **seller motivation is the #1 predictor of deal closure.**

---

## Tier Classification

| Tier | ARS Score | Recommended Action |
|---|---|---|
| **S** | 78–100 | Strong acquisition candidate — prioritize immediately |
| **A** | 60–77 | Good fit — worth a first call this quarter |
| **B** | 42–59 | Moderate fit — monitor, revisit in 6 months |
| **C** | 0–41 | Not ready — deprioritize |

---

## Project Structure

```
ars-engine/
├── backend/                        # FastAPI Python backend
│   ├── main.py                     # App entry point + lifespan hooks
│   ├── Dockerfile                  # Python 3.11-slim, non-root user
│   ├── railway.toml                # Railway deployment config
│   ├── requirements.txt
│   ├── .env.example                # All environment variables documented
│   ├── core/
│   │   ├── config.py               # Pydantic-settings configuration
│   │   ├── cache.py                # Async Redis client with graceful fallback
│   │   └── database.py             # Supabase client (optional persistence)
│   ├── models/
│   │   └── schemas.py              # All Pydantic request/response models
│   ├── routers/
│   │   ├── enrich.py               # All enrichment + export endpoints
│   │   └── health.py               # Health check + root endpoint
│   └── services/
│       ├── scorer.py               # ARS heuristic scoring + Claude AI enrichment
│       ├── scraper.py              # Web signal collection (httpx + BeautifulSoup)
│       ├── csv_parser.py           # Multi-format CSV ingestion
│       └── job_manager.py          # Async job lifecycle + Supabase persistence
├── frontend/
│   ├── index.html                  # Main SPA — dashboard, upload, results
│   ├── vs-saasquatch.html          # Feature comparison page
│   ├── roi-calculator.html         # ROI calculator for PE searchers
│   ├── sandbox.html                # API sandbox / demo mode
│   ├── login.html / signup.html    # Auth pages
│   ├── shared.css                  # Global design system tokens
│   ├── shared.js                   # Shared utilities
│   └── industries/                 # Industry-specific landing pages
│       ├── hvac.html
│       ├── landscaping.html
│       ├── plumbing.html
│       └── roofing.html
├── supabase/
│   └── migrations/
│       └── 001_initial.sql         # Full DB schema with indexes, RLS, views
├── sample_data/
│   └── sample_leads.csv            # 10 realistic SMB demo companies
├── nginx.conf                      # Static file server + API proxy config
├── docker-compose.yml              # Local dev: Redis + Backend + Frontend
└── render.yaml                     # One-click Render deployment config
```

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| **Frontend** | Vanilla HTML/CSS/JS | Single-file SPA, zero build step, instant deploy |
| **Backend** | FastAPI (Python 3.11) | Async, auto-generated OpenAPI docs at `/docs` |
| **AI Enrichment** | Anthropic Claude Sonnet | Acquisition analysis, risk flags, outreach emails |
| **Scraping** | httpx + BeautifulSoup | Homepage signals, job postings, tech stack detection |
| **Search** | Brave API / SerpAPI / DuckDuckGo | Web signal fallback chain — works without any key |
| **Database** | Supabase (Postgres) | Optional — in-memory store works without it |
| **Cache** | Redis / Upstash | 24hr TTL per company — deduplicates API costs |
| **Deployment** | Render (frontend + backend) | Free tier; `render.yaml` included for one-click setup |
| **Local Dev** | Docker Compose | Spins up Redis + Backend + Nginx frontend in one command |

---

## How It Works

```
┌──────────────────────────────────────────────────────────────────────┐
│                          ARS Engine Pipeline                         │
└──────────────────────────────────────────────────────────────────────┘

  CSV Upload / JSON POST
         │
         ▼
  ┌─────────────┐      ┌──────────────────────────────────────────┐
  │ CSV Parser  │─────▶│ Column normalization                     │
  │             │      │ Supports SaaSquatch, Apollo, Hunter.io,  │
  │             │      │ LinkedIn Sales Nav, and generic exports  │
  └─────────────┘      └──────────────────────────────────────────┘
         │
         ▼
  ┌─────────────┐      ┌──────────────────────────────────────────┐
  │  Job Store  │─────▶│ UUID job created, status = pending       │
  │  (memory /  │      │ Results stream back via polling          │
  │  Supabase)  │      └──────────────────────────────────────────┘
  └─────────────┘
         │
         ▼ (background task, parallel per company)
  ┌─────────────────────────────────────────────────────────────────┐
  │                     3-Phase Enrichment                          │
  │                                                                 │
  │  Phase 1 — Heuristic Scoring (instant)                         │
  │  ├── Exit signal scoring (regex patterns on description)       │
  │  ├── Financial proxy (revenue tier mapping)                    │
  │  ├── Operational leverage (employee count + tech signals)      │
  │  ├── Market tailwinds (industry classification)                │
  │  └── Competitive moat (keyword detection)                      │
  │                                                                 │
  │  Phase 2 — Web Scraping (async, parallel)                      │
  │  ├── Homepage scrape: founding year, tech stack, description   │
  │  ├── Search API: news, leadership signals, exit signals        │
  │  └── Job postings: COO / GM succession signals                 │
  │                                                                 │
  │  Phase 3 — AI Enrichment (Claude Sonnet)                       │
  │  ├── Acquisition thesis (2–3 sharp sentences)                  │
  │  ├── Risk flags (customer concentration, owner dependency)     │
  │  ├── Outreach angle (personalized to strongest signal)         │
  │  └── Email draft (founder-to-founder tone, ready to send)      │
  └─────────────────────────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────┐     ┌──────────────────────────────────────────┐
  │  Redis Cache │     │ 24hr TTL per company domain              │
  │              │     │ Re-importing same company hits cache —   │
  │              │     │ no wasted API credits                    │
  └──────────────┘     └──────────────────────────────────────────┘
         │
         ▼
  Ranked results (S/A/B/C) → Dashboard / CSV Export / Supabase
```

---

## API Endpoints

```
POST   /api/enrich              Submit companies for ARS enrichment (async, returns job_id)
POST   /api/enrich/csv          Upload CSV file — auto-parses, starts enrichment job
POST   /api/enrich/single       Synchronous single-company deep dive (~3–8s)
GET    /api/status/{job_id}     Poll job status — returns partial results as they stream in
GET    /api/export/{job_id}     Download scored results as CSV (all 11 columns including AI)
DELETE /api/job/{job_id}        Clean up completed job from memory
GET    /health                  System health: Supabase, Redis, Anthropic status
GET    /docs                    Interactive Swagger UI (auto-generated)
GET    /redoc                   ReDoc API documentation
```

### Example: Single Company Enrichment

```bash
curl -X POST https://your-api.onrender.com/api/enrich/single \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Apex Industrial Services",
    "industry": "Industrial Manufacturing",
    "location": "Cleveland OH",
    "employees": "310",
    "revenue_est": "$42M",
    "contact_name": "Frank Deluca",
    "contact_title": "President",
    "website": "apexindustrial.com",
    "description": "Second-generation family manufacturing business. Founder son not interested in taking over. Posted COO role on LinkedIn last month."
  }'
```

**Response:**
```json
{
  "company": "Apex Industrial Services",
  "tier": "S",
  "scores": {
    "ars": 82,
    "exit": 91,
    "financial": 73,
    "ops": 68,
    "tailwinds": 55,
    "moat": 62
  },
  "ai_enrichment": {
    "ai_analysis": "Apex Industrial is a Tier S acquisition target...",
    "risk_flags": "Second-generation transition risk — validate son's disengagement...",
    "outreach_angle": "Reference the active COO search as the succession hook.",
    "email_draft": "Subject: Partnership inquiry — Apex Industrial Services\n\n..."
  }
}
```

---

## CSV Format

Compatible with **SaaSquatch, Apollo.io, Hunter.io, and LinkedIn Sales Nav** exports. The parser normalizes column names automatically.

**Required column:** `company`

**Optional (improves scoring):** `industry`, `location`, `employees`, `revenue_est`, `contact_name`, `contact_title`, `email`, `website`, `description`

The parser handles alternate column names across export formats:

| Canonical Field | Also recognized as |
|---|---|
| `company` | `company_name`, `organization`, `business_name` |
| `contact_name` | `full_name`, `first_name` + `last_name` |
| `contact_title` | `title`, `job_title`, `position`, `role` |
| `employees` | `employee_count`, `headcount`, `team_size` |
| `revenue_est` | `annual_revenue`, `arr`, `rev` |
| `website` | `domain`, `url`, `company_url` |

See `sample_data/sample_leads.csv` for a working 10-company example.

---

## Scoring Formula

```
ARS = (Owner Exit × 0.30) + (Financial Health × 0.25) +
      (Operational Leverage × 0.20) + (Market Tailwinds × 0.15) +
      (Competitive Moat × 0.10)
```

### Exit Signal Detection

The scorer looks for the following patterns in the company description and scraped web content:

| Signal | Boost |
|---|---|
| Retirement / succession keywords | +35 |
| Active COO / GM job posting detected | +20 |
| "Family-owned", "second-generation" | +15 |
| Founder age 60+ detected | +20 |
| Business tenure 15–30 years | +15 |
| Explicit "exit" / "looking to sell" | +20 |

### Industry Classification

**High ICP** (strongest tailwinds + moat scores): HealthTech, FinTech, Data & Analytics, LegalTech, EdTech, AgTech, Clean Energy, IT Services

**Mid ICP**: Logistics & Supply Chain, Industrial Manufacturing, Professional Services, Life Sciences, HR, Food & Beverage, Construction

---

## Quick Start

### Option 1 — Docker (Recommended)

Starts Redis, the FastAPI backend, and the nginx frontend in one command:

```bash
git clone https://github.com/YOUR_USERNAME/ars-engine.git
cd ars-engine

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env — only ANTHROPIC_API_KEY is required

# Start everything
docker-compose up --build

# App:  http://localhost:3000
# API:  http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Option 2 — Manual Setup

**Prerequisites:** Python 3.11+, Redis (optional), Anthropic API key (optional)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY

uvicorn main:app --reload --port 8000

# Frontend (in a separate terminal)
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

### Demo Mode (Zero Config)

Run with no `.env` file at all. The engine uses heuristic-only scoring (no Claude API calls, no Redis, no Supabase). All endpoints work — you just get deterministic scores instead of AI-generated analysis.

---

## Environment Variables

```bash
# backend/.env

# ── REQUIRED ──────────────────────────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-your-key-here      # Powers AI enrichment + email drafts

# ── OPTIONAL: Supabase (persistent storage — skip for demo mode) ──────
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# ── OPTIONAL: Redis (caching — skip for demo mode) ────────────────────
REDIS_URL=redis://localhost:6379             # Use Upstash free tier for production

# ── OPTIONAL: Search APIs (improves signal scraping) ──────────────────
BRAVE_API_KEY=your-brave-key                # Preferred — better signal quality
SERPAPI_KEY=your-serpapi-key                # Fallback
# (no key = DuckDuckGo fallback — fully functional)

# ── APP CONFIG ─────────────────────────────────────────────────────────
APP_ENV=development
CORS_ORIGINS=http://localhost:3000
CACHE_TTL_SECONDS=86400                     # 24 hours
MAX_BATCH_SIZE=50
```

**Minimum viable setup:** Only `ANTHROPIC_API_KEY` is required for full AI features. Everything else degrades gracefully.

---

## Deployment on Render

The `render.yaml` in the repo root configures both services automatically.

### One-Click Deploy

1. Push this repo to GitHub (public)
2. Go to [render.com](https://render.com) → **New** → **Blueprint**
3. Connect your GitHub repo — Render detects `render.yaml` automatically
4. In the Render dashboard, add these environment variables to `ars-engine-backend`:
   - `ANTHROPIC_API_KEY` — your Anthropic key
   - `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` — optional, for persistence
   - `REDIS_URL` — optional, use [Upstash](https://upstash.com) free tier

5. Update `CORS_ORIGINS` in `render.yaml` to your frontend URL before deploying:
   ```yaml
   - key: CORS_ORIGINS
     value: https://ars-engine-frontend.onrender.com
   ```

Both services deploy on Render's **free tier**.

### Manual Render Deploy

```bash
# Backend — Web Service
# Runtime: Python | Root Dir: backend
# Build: pip install -r requirements.txt
# Start: uvicorn main:app --host 0.0.0.0 --port $PORT

# Frontend — Static Site
# Root Dir: frontend
# Publish Dir: .
```

---

## Database Setup (Supabase — Optional)

Without Supabase, all results are held in memory per job and lost on restart. To enable persistence:

1. Create a free project at [supabase.com](https://supabase.com)
2. Open **SQL Editor** → **New Query**
3. Paste the contents of `supabase/migrations/001_initial.sql` and run it

This creates:
- `enriched_companies` table with all ARS score columns, AI enrichment, and metadata
- `enrichment_jobs` table for job tracking
- Indexes on `ars_score`, `tier`, `industry`, and `exit_score` for fast filtering
- Row Level Security with service role access
- Two useful views: `tier_summary` and `top_targets`

```sql
-- Quick verify after setup:
select * from tier_summary;
select * from top_targets limit 10;
```

---

## Architecture

```
┌─────────────────┐       ┌──────────────────────┐       ┌─────────────────┐
│   Frontend      │──────▶│   FastAPI Backend     │──────▶│  Supabase DB    │
│   (Render       │       │   (Render Web Service)│       │  (Postgres)     │
│   Static Site)  │       └──────────────────────┘       └─────────────────┘
└─────────────────┘                 │                              │
                                    │                       ┌──────┴──────┐
                             ┌──────┴──────┐                │  In-Memory  │
                             │   Redis     │                │  Job Store  │
                             │   Cache     │                │  (fallback) │
                             └─────────────┘                └─────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                       ▼
      ┌─────────────┐     ┌──────────────────┐    ┌──────────────┐
      │ Web Scraper │     │  Search API      │    │  Anthropic   │
      │ httpx+BS4   │     │  Brave → SerpAPI │    │  Claude      │
      │ Homepage    │     │  → DuckDuckGo    │    │  Sonnet      │
      └─────────────┘     └──────────────────┘    └──────────────┘
```

---

## Key Design Decisions

**Why FastAPI over Node.js?**
Python-native AI/ML libraries, clean async support, and auto-generated OpenAPI docs at `/docs`. No additional tooling needed.

**Why in-memory job store instead of Celery?**
Zero infrastructure dependencies in demo mode. The in-memory store covers the full job lifecycle. Supabase persistence activates transparently when configured. Celery + SQS/RabbitMQ can be layered on for production scale without changing the API contract.

**Why cache at the company domain level?**
Re-importing the same company from different CSV exports reuses the cached result — no duplicate API calls, no wasted credits. 24-hour TTL ensures signals stay fresh.

**Why vanilla JS for the frontend?**
Zero build step means instant deployment to any static host. The SPA is fully functional without Node, webpack, or a CI pipeline. Reduces the onboarding friction for evaluators running it locally.

**Why graceful degradation on every service?**
The engine is fully functional with zero external services configured. Redis missing → no cache. Supabase missing → in-memory store. Anthropic key missing → heuristic fallback. Brave/SerpAPI missing → DuckDuckGo. This means the tool works in a reviewer's local environment with nothing but `pip install`.

---

## Business Case

For a PE searcher spending 6 hours/week manually qualifying companies:

| | Before ARS | After ARS |
|---|---|---|
| Time to qualify 50 companies | 6 hours | 20 minutes |
| Outreach email quality | Generic templates | AI-personalized per signal |
| Deal prioritization | Gut feel | Data-driven S/A/B/C tiers |
| Signal source | LinkedIn + gut | Web scraping + AI analysis |

```
Time saved:      ~5.5 hours/week
At $100/hour:    $28,600/year in recovered productivity
Tool cost:       $199/month → $2,388/year
ROI:             ~12x
```

---

## Roadmap

- [ ] CRM push — HubSpot and Salesforce one-click export
- [ ] Founder LinkedIn enrichment via Proxycurl
- [ ] Auto re-scoring on signal change detection (weekly cron)
- [ ] SEC EDGAR financial proxy for larger SMBs
- [ ] Slack alerts on tier upgrades
- [ ] Multi-tenant auth via Supabase magic link
- [ ] PDF scorecard export per company
- [ ] Webhook support for CRM integrations

---

## License

MIT — use freely, build boldly.

---

*Built for Caprae Capital's Full Stack Developer challenge. Extends SaaSquatch's lead generation capability with PE-specific acquisition intelligence.*
