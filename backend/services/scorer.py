"""
ARS Scoring Engine
Two-phase scoring:
  Phase 1 — Heuristic: fast, deterministic, runs on import
  Phase 2 — AI: Claude-powered deep analysis, runs async
"""
import re
import random
from typing import Dict, Any, Optional, Tuple
from models.schemas import ARSScores, TierEnum, AIEnrichment, CompanyInput
from core.config import get_settings
import anthropic


# ── INDUSTRY CLASSIFICATIONS ──────────────────────────────────────────────────
HIGH_ICP = {
    "HealthTech", "FinTech", "Data & Analytics", "LegalTech",
    "EdTech", "AgTech", "Clean Energy", "IT Services"
}
MID_ICP = {
    "Logistics & Supply Chain", "Industrial Manufacturing",
    "Professional Services", "Life Sciences", "Human Resources",
    "Food & Beverage", "Construction"
}
HIGH_TAILWIND = {
    "HealthTech", "FinTech", "Clean Energy", "Data & Analytics",
    "AgTech", "LegalTech", "EdTech"
}
MID_TAILWIND = {
    "IT Services", "Logistics & Supply Chain", "Life Sciences",
    "Industrial Manufacturing"
}

# ── EXIT SIGNAL PATTERNS ──────────────────────────────────────────────────────
EXIT_PATTERNS = [
    (r'\b(retire|retirement|stepping down|succession)\b', 35),
    (r'\b(coo role|gm role|general manager|operations director)\b', 25),
    (r'\b(family.owned|second.generation|founder.owned)\b', 15),
    (r'\b(age[sd]? \d{2}|aged \d{2}|\b6[0-9] year)\b', 20),
    (r'\b(1[5-9] years|2[0-9] years|30 years)\b', 15),
    (r'\b(exit|looking to sell|transition)\b', 20),
]


def heuristic_score(lead: CompanyInput, scraped: Optional[Dict] = None) -> ARSScores:
    """
    Fast heuristic scoring. Runs instantly on import.
    Seeded by company name for reproducibility.
    """
    seed = sum(ord(c) for c in lead.company)
    rng = random.Random(seed)

    desc = (lead.description or "").lower()
    signals = lead.signals or []
    scraped = scraped or {}

    # ── OWNER EXIT (weight: 30%) ──────────────────────────────────────────────
    exit_score = 30
    for pattern, boost in EXIT_PATTERNS:
        if re.search(pattern, desc, re.I):
            exit_score += boost
    if scraped.get("has_coo_posting"):
        exit_score += 20
    if scraped.get("has_gm_posting"):
        exit_score += 15
    if scraped.get("founding_year"):
        age = 2025 - scraped["founding_year"]
        if age >= 20:
            exit_score += 20
        elif age >= 15:
            exit_score += 12
        elif age >= 10:
            exit_score += 6
    exit_score += rng.randint(0, 8)
    exit_score = min(97, exit_score)

    # ── FINANCIAL HEALTH (weight: 25%) ────────────────────────────────────────
    fin_score = 35
    rev = lead.revenue_est or ""
    rev_tiers = [
        (["$80M", "$100M", "$120M", "$60M"], 65),
        (["$30M", "$40M", "$50M"], 55),
        (["$15M", "$18M", "$20M", "$25M", "$28M", "$32M"], 45),
        (["$8M", "$10M", "$12M"], 35),
        (["$3M", "$4M", "$5M", "$6M", "$7M"], 20),
    ]
    for tokens, base in rev_tiers:
        if any(t in rev for t in tokens):
            fin_score = base + rng.randint(0, 18)
            break
    if "growth" in signals:
        fin_score += 10
    if "funding" in signals:
        fin_score += 8
    if "pain" in signals:
        fin_score -= 10
    fin_score = max(10, min(97, fin_score))

    # ── OPERATIONAL LEVERAGE (weight: 20%) ────────────────────────────────────
    ops_score = 35
    emp = lead.employees or ""
    emp_map = [
        (["500", "1000"], 25),
        (["250"], 18),
        (["100"], 12),
        (["50", "100"], 8),
    ]
    for tokens, boost in emp_map:
        if any(t in emp for t in tokens):
            ops_score += boost
            break
    if "tech" in signals:
        ops_score += 12
    if scraped.get("tech_stack"):
        ops_score += min(10, len(scraped["tech_stack"]) * 2)
    if lead.industry in HIGH_ICP:
        ops_score += 8
    ops_score += rng.randint(0, 10)
    ops_score = min(97, ops_score)

    # ── MARKET TAILWINDS (weight: 15%) ────────────────────────────────────────
    if lead.industry in HIGH_TAILWIND:
        tail_score = 65 + rng.randint(0, 25)
    elif lead.industry in MID_TAILWIND:
        tail_score = 48 + rng.randint(0, 20)
    else:
        tail_score = 28 + rng.randint(0, 20)
    tail_score = min(97, tail_score)

    # ── COMPETITIVE MOAT (weight: 10%) ────────────────────────────────────────
    moat_score = 30
    moat_kws = ["niche", "specialist", "market leader", "proprietary", "patent",
                "exclusive", "dominant", "category", "only provider"]
    for kw in moat_kws:
        if kw in desc:
            moat_score += 12
            break
    if "funding" in signals:
        moat_score += 15
    if lead.industry in HIGH_ICP:
        moat_score += 10
    moat_score += rng.randint(0, 12)
    moat_score = min(97, moat_score)

    # ── ARS COMPOSITE ─────────────────────────────────────────────────────────
    ars = round(
        exit_score   * 0.30 +
        fin_score    * 0.25 +
        ops_score    * 0.20 +
        tail_score   * 0.15 +
        moat_score   * 0.10
    )
    ars = min(97, ars)

    return ARSScores(
        ars=ars,
        exit=exit_score,
        financial=fin_score,
        ops=ops_score,
        tailwinds=tail_score,
        moat=moat_score,
    )


def get_tier(ars: int) -> TierEnum:
    if ars >= 78:
        return TierEnum.S
    if ars >= 60:
        return TierEnum.A
    if ars >= 42:
        return TierEnum.B
    return TierEnum.C


async def ai_enrich(lead: CompanyInput, scores: ARSScores, scraped: Dict) -> AIEnrichment:
    """
    Phase 2: Claude-powered deep acquisition analysis.
    Returns AI analysis, risk flags, and tailored outreach email.
    """
    settings = get_settings()

    # Build rich context from scraped signals
    scraped_context = ""
    if scraped.get("founding_year"):
        scraped_context += f"\n- Business founded: {scraped['founding_year']} ({2025 - scraped['founding_year']} years old)"
    if scraped.get("has_coo_posting"):
        scraped_context += "\n- CONFIRMED: Active COO/GM job posting detected (strong succession signal)"
    if scraped.get("exit_signals"):
        scraped_context += f"\n- Web exit signals found: {', '.join(scraped['exit_signals'][:5])}"
    if scraped.get("growth_signals"):
        scraped_context += f"\n- Web growth signals: {', '.join(scraped['growth_signals'][:4])}"
    if scraped.get("tech_stack"):
        scraped_context += f"\n- Tech stack detected: {', '.join(scraped['tech_stack'])}"
    if scraped.get("news_snippets"):
        scraped_context += f"\n- Recent web context: {scraped['news_snippets'][0][:200]}"

    prompt = f"""You are a senior acquisition analyst at an ETA (Entrepreneurship Through Acquisition) private equity fund focused on lower-middle-market SMB acquisitions.

Analyze this company as a potential acquisition target and provide a structured assessment.

COMPANY DATA:
- Company: {lead.company}
- Industry: {lead.industry}
- Location: {lead.location}
- Employees: {lead.employees}
- Revenue: {lead.revenue_est}
- Contact: {lead.contact_name}, {lead.contact_title}
- Buying signals: {', '.join(lead.signals) if lead.signals else 'none identified'}
- Description: {lead.description}

ARS SCORES:
- Composite ARS: {scores.ars}/100 (Tier {get_tier(scores.ars).value})
- Owner Exit Signal: {scores.exit}/100
- Financial Health: {scores.financial}/100
- Operational Leverage: {scores.ops}/100
- Market Tailwinds: {scores.tailwinds}/100
- Competitive Moat: {scores.moat}/100

SCRAPED INTELLIGENCE:{scraped_context if scraped_context else ' No additional web signals available.'}

Provide your response in EXACTLY this format (no extra text outside these blocks):

ANALYSIS: [2-3 sharp sentences. State your acquisition thesis or why it's not a fit. Reference the strongest signal specifically. Be direct — no hedging.]

RISK: [1-2 sentences on the most critical risk to this acquisition. Be specific — mention customer concentration, owner dependency, market risk, or operational gaps.]

OUTREACH_ANGLE: [One sentence: the specific angle to use in first contact based on the signals above.]

EMAIL_SUBJECT: [Subject line for acquisition inquiry email — professional, not salesy]

EMAIL_BODY: [3 short paragraphs. Tone: respectful, founder-to-founder, acquisition inquiry. Reference something specific about their business. Do NOT include a greeting line — start directly with paragraph 1. Do NOT say "I hope this finds you well." Be direct and human.]"""

    if not settings.anthropic_api_key:
        # No API key — return heuristic-based fallback immediately
        return _heuristic_fallback(lead, scores)

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        text = message.content[0].text

        # Parse structured response
        analysis_m = re.search(r'ANALYSIS:\s*([\s\S]*?)(?=RISK:|$)', text)
        risk_m = re.search(r'RISK:\s*([\s\S]*?)(?=OUTREACH_ANGLE:|$)', text)
        angle_m = re.search(r'OUTREACH_ANGLE:\s*(.+)', text)
        subject_m = re.search(r'EMAIL_SUBJECT:\s*(.+)', text)
        body_m = re.search(r'EMAIL_BODY:\s*([\s\S]+)', text)

        analysis = analysis_m.group(1).strip() if analysis_m else text[:350]
        risk = risk_m.group(1).strip() if risk_m else None
        angle = angle_m.group(1).strip() if angle_m else None
        subject = subject_m.group(1).strip() if subject_m else f"Acquisition inquiry — {lead.company}"
        body = body_m.group(1).strip() if body_m else "Unable to generate email."
        email_draft = f"Subject: {subject}\n\n{body}"

        return AIEnrichment(
            ai_analysis=analysis,
            risk_flags=risk,
            email_draft=email_draft,
            outreach_angle=angle,
        )

    except Exception:
        return _heuristic_fallback(lead, scores)


def _heuristic_fallback(lead: CompanyInput, scores: ARSScores) -> AIEnrichment:
    """
    Heuristic-only enrichment — used when ANTHROPIC_API_KEY is not set,
    or as a fallback if the API call fails.
    Produces deterministic, signal-driven output with zero API cost.
    """
    tier = get_tier(scores.ars)

    # Build signal-aware analysis
    exit_note = (
        "strong owner exit signals detected — a succession event may be imminent"
        if scores.exit >= 65
        else "moderate exit readiness — monitor for succession triggers"
    )
    fin_note = (
        "financials suggest a healthy, cash-generating business"
        if scores.financial >= 60
        else "revenue profile is early-stage or undisclosed — validate before advancing"
    )
    moat_note = (
        f"operates in a niche {lead.industry} segment with defensible positioning"
        if scores.moat >= 55
        else f"competes in a fragmented {lead.industry} market — assess differentiation"
    )

    analysis = (
        f"{lead.company} is a Tier {tier.value} acquisition target in {lead.industry}. "
        f"With {lead.employees or 'undisclosed'} employees and {lead.revenue_est or 'undisclosed revenue'}, "
        f"the business shows {exit_note}. {fin_note.capitalize()}. "
        f"{'Description: ' + lead.description[:120] + '.' if lead.description else moat_note.capitalize() + '.'}"
    )

    # Score-driven risk flag
    if scores.exit < 40:
        risk = "Low exit signal — owner may not be motivated to sell. Validate succession intent before investing outreach time."
    elif scores.financial < 40:
        risk = "Weak financial proxy — revenue or growth signals are thin. Request P&L before advancing to LOI."
    else:
        risk = "Verify customer concentration and owner dependency before proceeding to LOI."

    # Outreach angle based on strongest signal
    if scores.exit >= 65:
        angle = f"Reference the business's tenure and ask about long-term ownership plans — succession is the likely hook."
    elif scores.financial >= 65:
        angle = f"Lead with {lead.company}'s strong market position and offer a growth capital conversation."
    elif scores.tailwinds >= 65:
        angle = f"Reference {lead.industry} tailwinds and position as a partner to accelerate — not just a buyer."
    else:
        angle = f"Reference {lead.company}'s {lead.industry} market position and founder journey."

    email_draft = (
        f"Subject: Exploring a potential partnership with {lead.company}\n\n"
        f"I've been following {lead.company}'s work in the {lead.industry} space and wanted to reach out directly. "
        f"We're an acquisition fund that focuses specifically on partnering with founder-led businesses in your segment — "
        f"not to flip them, but to grow them over a multi-year horizon.\n\n"
        f"Given {lead.company}'s position in the market, I believe there could be a compelling fit worth exploring. "
        f"Our approach is to preserve what makes a business successful while providing the capital and operational support to take it further.\n\n"
        f"Would you be open to a 15-minute call this week? No pitch — just an honest conversation about your goals for the business.\n\n"
        f"Best,\n[Your name]"
    )

    return AIEnrichment(
        ai_analysis=analysis,
        risk_flags=risk,
        email_draft=email_draft,
        outreach_angle=angle,
    )
