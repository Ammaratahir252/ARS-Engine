# ARS Engine — Acquisition Readiness Score for PE Deal Sourcing

> Transform raw business lists into ranked acquisition targets using AI-powered signal analysis.

Built as part of Caprae Capital's Full Stack Developer challenge.  
Extends SaaSquatch's lead generation capability with PE-specific acquisition intelligence.

---

## What It Does

Upload a CSV of companies. Get back every company scored 0–100 across five acquisition-readiness dimensions — with plain-English AI rationale, risk flags, and a tailored outreach angle for each target.

**The five scoring dimensions:**
- **Owner Exit Signals** (founder age, succession hiring, business tenure)
- **Financial Health Proxy** (revenue trajectory, hiring trends, web presence growth)
- **Operational Leverage** (team depth, systematization signals, tech maturity)
- **Market Tailwinds** (industry growth/contraction context)
- **Competitive Moat** (niche positioning, customer concentration risk)

---

## Project Structure

```
ars-engine/
├── backend/                    # FastAPI Python backend
│   ├── main.py                 # App entry point
│   ├── Dockerfile
│   ├── railway.toml            # Railway deployment config
│   ├── requirements.txt
│   ├── .env.example
│   ├── core/
│   │   ├── config.py           # Settings (pydantic-settings)
│   │   ├── cache.py            # Redis async client
│   │   └── database.py         # Supabase client
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   ├── routers/
│   │   ├── enrich.py           # All enrichment endpoints
│   │   └── health.py           # Health check
│   └── services/
│       ├── scorer.py           # ARS heuristic + Claude AI scoring
│       ├── scraper.py          # Web signal collection
│       ├── csv_parser.py       # CSV ingestion (Apollo/Hunter/SaaSquatch)
│       └── job_manager.py      # Async job lifecycle
├── frontend/
│   └── index.html              # Single-page app (vanilla JS + CSS)
├── supabase/
│   └── migrations/
│       └── 001_initial.sql     # Full DB schema
├── sample_data/
│   └── sample_leads.csv        # 10 demo SMB companies
├── nginx.conf                  # Frontend static serving config
├── docker-compose.yml          # Local dev (Redis + Backend + Frontend)
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla HTML/CSS/JS (single file, zero build step) |
| Backend | FastAPI (Python 3.11) |
| Database | Supabase (Postgres) |
| Cache | Redis (local) / Upstash (production) |
| AI | Anthropic Claude claude-sonnet-4-20250514 |
| Scraping | httpx + BeautifulSoup + DuckDuckGo/Brave/SerpAPI |
| Deployment | Frontend → nginx/Vercel \| Backend → Railway |

---

## Quick Start (Docker — Recommended)

```bash
git clone https://github.com/yourusername/ars-engine.git
cd ars-engine

# 1. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env — add your ANTHROPIC_API_KEY (required)

# 2. Start everything
docker-compose up --build

# App: http://localhost:3000
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

---

## Manual Setup

### Prerequisites
- Python 3.11+
- Redis (local or Upstash)
- Anthropic API key

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

uvicorn main:app --reload --port 8000
```

### Frontend

Serve the `frontend/` folder with any static server:

```bash
# Python built-in
cd frontend && python -m http.server 3000

# Or use the nginx Docker container from docker-compose
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ Yes | Powers AI enrichment and email drafting |
| `SUPABASE_URL` | Optional | Enables persistent storage |
| `SUPABASE_SERVICE_KEY` | Optional | Supabase service role key |
| `REDIS_URL` | Optional | Enables caching (default: `redis://localhost:6379`) |
| `SERPAPI_KEY` | Optional | Better web signal search |
| `BRAVE_API_KEY` | Optional | Alternative search API |
| `HUNTER_API_KEY` | Optional | Email verification |
| `APP_ENV` | Optional | `development` or `production` |
| `MAX_BATCH_SIZE` | Optional | Max companies per batch (default: 50) |

**Minimum viable setup:** only `ANTHROPIC_API_KEY` is required. Everything else degrades gracefully.

---

## Database Setup (Supabase — Optional)

Without Supabase, results are stored in-memory per job (lost on restart). To enable persistence:

1. Create a free project at [supabase.com](https://supabase.com)
2. Open SQL Editor → New Query
3. Paste and run `supabase/migrations/001_initial.sql`
4. Copy your project URL and service role key into `backend/.env`

---

## API Endpoints

```
POST /api/enrich              Submit companies for ARS enrichment (returns job_id)
POST /api/enrich/csv          Upload CSV file for enrichment
POST /api/enrich/single       Synchronous single-company deep dive
GET  /api/status/{job_id}     Poll job status + get results as they stream in
GET  /api/export/{job_id}     Download scored results as CSV
DELETE /api/job/{job_id}      Clean up job from memory
GET  /health                  System health (Supabase, Redis, Anthropic status)
GET  /docs                    Interactive Swagger UI
```

---

## CSV Format

Compatible with SaaSquatch, Apollo.io, Hunter.io, and LinkedIn Sales Nav exports.

Required: `company`  
Optional (but improves scoring): `industry`, `location`, `employees`, `revenue_est`, `contact_name`, `contact_title`, `email`, `website`, `description`

See `sample_data/sample_leads.csv` for a working example.

---

## Scoring Methodology

```
ARS = (Owner Exit × 0.30) + (Financial Health × 0.25) +
      (Operational Leverage × 0.20) + (Market Tailwinds × 0.15) +
      (Competitive Moat × 0.10)
```

Owner exit signals are weighted highest because in ETA, seller motivation is the #1 predictor of deal closure.

### Tier Classification

| Tier | ARS | Action |
|---|---|---|
| **S** | 78–100 | Strong acquisition candidate — prioritize immediately |
| **A** | 60–77 | Good fit — worth a first call this quarter |
| **B** | 42–59 | Moderate fit — monitor, revisit in 6 months |
| **C** | 0–41 | Not ready — deprioritize |

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Frontend       │────▶│  FastAPI Backend  │────▶│  Supabase DB    │
│  (nginx/Vercel) │     │  (Railway)        │     │  (Postgres)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │                        │
                         ┌──────▼──────┐         ┌──────▼──────┐
                         │  Redis      │         │  Job Store  │
                         │  Cache      │         │  (memory)   │
                         └─────────────┘         └─────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
      ┌─────────────┐  ┌─────────────┐  ┌──────────────┐
      │ Web Scraper │  │  Search API │  │ Anthropic    │
      │ httpx+BS4   │  │  Brave/DDG  │  │ Claude API   │
      └─────────────┘  └─────────────┘  └──────────────┘
```

---

## Key Design Decisions

**Why FastAPI over Node.js?**  
Python-native AI/ML libraries, clean async support, and auto-generated OpenAPI docs.

**Why in-memory job store instead of Celery?**  
Zero infra dependencies for demo mode. Supabase persistence kicks in when configured. Celery can be added for production scale.

**Why Claude Sonnet?**  
Precise instruction-following for structured output (5-dimension scores + rationale). Graceful fallback to heuristic scoring if API is unavailable.

**Why cache at domain level?**  
Re-importing the same company from different CSVs reuses the cached result — no wasted API credits. 24-hour TTL.

---

## Roadmap

- [ ] CRM push (HubSpot, Salesforce)
- [ ] Founder LinkedIn enrichment via Proxycurl
- [ ] Auto re-scoring on signal change detection
- [ ] SEC EDGAR financial proxy for larger SMBs
- [ ] Slack alerts on tier upgrades
- [ ] Multi-tenant auth (Supabase magic link)

---

## Business Case

For a PE searcher spending 6 hours/week on manual company qualification:

- Time saved: ~5.5 hours/week
- At $100/hour: **$28,600/year** in recovered productivity
- Tool cost at $199/month: $2,388/year
- **ROI: ~12x**

---

## License

MIT — use freely, build boldly.
