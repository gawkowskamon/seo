# SEO Article Writer - PRD

## Original Problem Statement
Aplikacja do pisania artykulow blogowych zwiazanych z ksiegowoscia, zoptymalizowana pod SEO AI.

## Tech Stack
- Backend: FastAPI + MongoDB (Motor async + PyMongo sync for threads)
- Frontend: React + Shadcn UI + Recharts
- AI: OpenAI gpt-4.1-mini, gpt-5.2, Gemini nano-banana via Emergent LLM Key

## Critical Architecture: ThreadPoolExecutor for ALL LLM calls
All LLM-calling background tasks use run_in_executor + sync PyMongo + asyncio.new_event_loop()

Migrated endpoints:
- Article generation, SEO Assistant, Image generation, Batch image generation
- SEO Audit, Competition analysis, Keyword analytics, AI Rewriter
- AI Article Suggestions, Plagiarism Checker, Content Verification

## Credentials
- Admin: ADMIN_EMAIL / ADMIN_PASSWORD (z .env)
- WordPress: monika.gawkowska@kurdynowski.pl / jY67 vfXG WSqw Wic4 LRRg CJUw
- WordPress URL: https://kurdynowski.com.pl/cms-biuro

## SEO Scoring (14 dimensions, max 104 pts)
- title (12), meta_description (8), content_length (8), headings (12), keywords (12)
- toc (6), faq (8), internal_links (4), sources_eeat (10), slug (4)
- formatting (8), readability (6), freshness (3), meta_title (3)

## Completed Features
- [x] Article generation with AI (GPT) - enhanced prompts for reliability
- [x] Visual editor with formatting toolbar + HTML view
- [x] Topic suggestions
- [x] AI SEO Assistant with Apply All
- [x] Image generator (Nano Banana)
- [x] Content templates (standard, listicle, case study)
- [x] Series article generation
- [x] JWT authentication, multi-client workspaces, admin role
- [x] PDF and HTML export
- [x] WordPress integration
- [x] Subscription system (TPay)
- [x] Content Calendar
- [x] Scheduled WordPress Publishing
- [x] Automatic Internal Link Building
- [x] Article Import from URL
- [x] AI Chat Assistant
- [x] Dark Mode
- [x] Keyword Analytics Dashboard
- [x] AI Rewriter
- [x] Newsletter Generator
- [x] AI Article Suggestions (2026-03-23)
- [x] Performance Dashboard (2026-03-23)
- [x] Plagiarism Checker (2026-03-23)
- [x] Enhanced SEO Scorer - E-E-A-T, slug, formatting, freshness, readability (2026-03-23)
- [x] Enhanced Article Generator - legal refs, concrete data, credible sources (2026-03-23)
- [x] Content Verification / Fact-Check panel (2026-03-23)

## Backlog (P2+)
- [ ] Powiadomienia email o potrzebie aktualizacji artykulow
- [ ] WordPress export stylizacja (identyczna jak edytor)
- [ ] A/B Testing tytulow
- [ ] Integracja Social Media
- [ ] Masowe operacje na artykulach
- [ ] Historia wersji artykulow
- [ ] Auto generowanie meta tagow
