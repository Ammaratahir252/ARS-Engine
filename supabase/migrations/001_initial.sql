-- ARS Engine — Supabase Schema
-- Run this in your Supabase SQL Editor
-- Dashboard → SQL Editor → New Query → Paste → Run

-- ── ENRICHED COMPANIES ───────────────────────────────────────────────────────
create table if not exists enriched_companies (
  id              uuid primary key default gen_random_uuid(),
  company         text not null,
  industry        text,
  location        text,
  employees       text,
  revenue_est     text,
  contact_name    text,
  contact_title   text,
  email           text,
  website         text,
  signals         text[],
  description     text,

  -- ARS Scores
  ars_score       int check (ars_score between 0 and 100),
  exit_score      int check (exit_score between 0 and 100),
  financial_score int check (financial_score between 0 and 100),
  ops_score       int check (ops_score between 0 and 100),
  tailwinds_score int check (tailwinds_score between 0 and 100),
  moat_score      int check (moat_score between 0 and 100),
  tier            text check (tier in ('S', 'A', 'B', 'C')),

  -- AI Enrichment
  ai_analysis     text,
  risk_flags      text,
  email_draft     text,
  outreach_angle  text,

  -- Metadata
  created_at      timestamptz default now(),
  updated_at      timestamptz default now(),
  scored_at       timestamptz,

  -- Unique constraint: one record per company domain
  constraint unique_company_website unique (company, website)
);

-- ── ENRICHMENT JOBS ──────────────────────────────────────────────────────────
create table if not exists enrichment_jobs (
  id          uuid primary key default gen_random_uuid(),
  status      text default 'pending' check (status in ('pending', 'processing', 'completed', 'failed')),
  total       int default 0,
  completed   int default 0,
  failed      int default 0,
  created_at  timestamptz default now(),
  updated_at  timestamptz default now()
);

-- ── INDEXES ───────────────────────────────────────────────────────────────────
create index if not exists idx_companies_ars      on enriched_companies(ars_score desc);
create index if not exists idx_companies_tier     on enriched_companies(tier);
create index if not exists idx_companies_industry on enriched_companies(industry);
create index if not exists idx_companies_exit     on enriched_companies(exit_score desc);
create index if not exists idx_companies_company  on enriched_companies(company);

-- ── ROW LEVEL SECURITY ────────────────────────────────────────────────────────
-- Enable RLS (service key bypasses this)
alter table enriched_companies enable row level security;
alter table enrichment_jobs    enable row level security;

-- Allow service role full access (your backend uses service key)
create policy "service_role_all" on enriched_companies
  for all using (auth.role() = 'service_role');

create policy "service_role_all_jobs" on enrichment_jobs
  for all using (auth.role() = 'service_role');

-- ── UPDATED_AT TRIGGER ────────────────────────────────────────────────────────
create or replace function update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger set_updated_at
  before update on enriched_companies
  for each row execute function update_updated_at();

-- ── USEFUL VIEWS ─────────────────────────────────────────────────────────────
create or replace view tier_summary as
  select
    tier,
    count(*) as count,
    round(avg(ars_score)) as avg_ars,
    round(avg(exit_score)) as avg_exit,
    max(ars_score) as top_score
  from enriched_companies
  group by tier
  order by
    case tier when 'S' then 1 when 'A' then 2 when 'B' then 3 when 'C' then 4 end;

create or replace view top_targets as
  select company, industry, location, ars_score, exit_score, tier, contact_name, email
  from enriched_companies
  where tier in ('S', 'A')
  order by ars_score desc, exit_score desc;

-- Done! Your ARS Engine schema is ready.
-- Verify: select count(*) from enriched_companies;
