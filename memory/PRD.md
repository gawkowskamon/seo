# SEO Article Writer - PRD

## Original Problem Statement
Aplikacja do pisania artykulow blogowych zwiazanych z ksiegowoscia, zoptymalizowana pod SEO AI.

## Tech Stack
- Backend: FastAPI + MongoDB (Motor async + PyMongo sync for threads)
- Frontend: React + Shadcn UI + Recharts
- AI: OpenAI gpt-4.1-mini via Emergent LLM Key
- Scraping: httpx + BeautifulSoup (DuckDuckGo HTML)

## Critical Architecture
All LLM tasks use ThreadPoolExecutor + sync PyMongo + asyncio.new_event_loop()
Frontend polls GET /status/{job_id} endpoints until completed/failed

## Credentials
- Admin: ADMIN_EMAIL / ADMIN_PASSWORD (z .env)
- WordPress: monika.gawkowska@kurdynowski.pl / jY67 vfXG WSqw Wic4 LRRg CJUw
- WordPress URL: https://kurdynowski.com.pl/cms-biuro

## SEO Scoring (14 dimensions, max 104 pts)
title(12), meta_description(8), content_length(8), headings(12), keywords(12), toc(6), faq(8), internal_links(4), sources_eeat(10), slug(4), formatting(8), readability(6), freshness(3), meta_title(3)

## All Completed Features
- [x] AI Article generation (enhanced E-E-A-T, legal refs, concrete data)
- [x] Visual editor + HTML view + formatting toolbar
- [x] Topic suggestions + AI Article Suggestions
- [x] AI SEO Assistant + Apply All
- [x] Image generator (Nano Banana) + batch
- [x] Content templates (standard, listicle, case study)
- [x] Series article generation
- [x] JWT auth, multi-client workspaces, admin role (auto-seeded)
- [x] PDF and HTML export
- [x] WordPress integration (styled inline export)
- [x] Subscription system (TPay - mocked)
- [x] Content Calendar + Scheduled WordPress Publishing
- [x] Automatic Internal Link Building
- [x] Article Import from URL
- [x] AI Chat Assistant, AI Rewriter
- [x] Dark Mode
- [x] Keyword Analytics Dashboard
- [x] Newsletter Generator
- [x] Performance Dashboard (admin, DAU/MAU, charts)
- [x] Plagiarism Checker
- [x] Content Verification / Fact-Check
- [x] Enhanced SEO Scorer (14 dimensions)
- [x] Auto Competition Analysis (DuckDuckGo scraping + AI comparison)
- [x] A/B Title Testing (5 variants, CTR/SEO/Emotion/Clarity scores)
- [x] Bulk Article Operations (select, delete, categorize) (2026-03-23)
- [x] Auto Meta Tag Generation (3 title + 3 desc variants + recommended) (2026-03-23)
- [x] Article Version History (auto-save on edit, view/restore) (2026-03-23)
- [x] Smart Publishing Schedule (AI suggests best day/time) (2026-03-23)

## Backlog
- [ ] Integracja Social Media (generowanie postów promujących)
- [ ] Powiadomienia email o potrzebie aktualizacji artykułów
