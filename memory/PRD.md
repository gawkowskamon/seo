# SEO Article Writer - PRD

## Original Problem Statement
Aplikacja do pisania artykulow blogowych zwiazanych z ksiegowoscia, zoptymalizowana pod SEO AI.

## Tech Stack
- Backend: FastAPI + MongoDB (Motor async + PyMongo sync for threads)
- Frontend: React + Shadcn UI + Recharts
- AI: OpenAI gpt-4.1-mini via Emergent LLM Key
- Scraping: httpx + BeautifulSoup (DuckDuckGo)

## Critical Architecture
All LLM tasks use ThreadPoolExecutor + sync PyMongo + asyncio.new_event_loop()

## Credentials
- Admin: ADMIN_EMAIL / ADMIN_PASSWORD (z .env)
- WordPress: monika.gawkowska@kurdynowski.pl / jY67 vfXG WSqw Wic4 LRRg CJUw

## All Completed Features (30+)
- [x] AI Article generation (E-E-A-T, legal refs, concrete data)
- [x] Visual editor + HTML view + formatting toolbar
- [x] Topic suggestions + AI Article Suggestions
- [x] AI SEO Assistant + Apply All
- [x] Image generator (Nano Banana) + batch
- [x] Content templates (standard, listicle, case study)
- [x] Series article generation
- [x] JWT auth, multi-client workspaces, admin role
- [x] PDF and HTML export
- [x] WordPress integration (styled inline export)
- [x] Subscription system (TPay - mocked)
- [x] Content Calendar + Scheduled WordPress Publishing
- [x] Internal Link Building + Article Import from URL
- [x] AI Chat Assistant + AI Rewriter
- [x] Dark Mode
- [x] Keyword Analytics Dashboard + Newsletter Generator
- [x] Performance Dashboard (admin, DAU/MAU, charts)
- [x] Plagiarism Checker + Content Verification / Fact-Check
- [x] Enhanced SEO Scorer (14 dimensions, E-E-A-T)
- [x] Auto Competition Analysis (DuckDuckGo scraping + AI)
- [x] A/B Title Testing (5 variants, CTR/SEO/Emotion/Clarity)
- [x] Bulk Article Operations (select, delete, categorize)
- [x] Auto Meta Tag Generation (3+3 variants + recommended)
- [x] Article Version History (auto-save, view, restore)
- [x] Smart Publishing Schedule (AI best day/time)
- [x] Social Media Post Generator (LinkedIn/Twitter/Facebook/Instagram × 3 tones + copy) (2026-03-23)

## Backlog
- [ ] Powiadomienia email o potrzebie aktualizacji artykułów
