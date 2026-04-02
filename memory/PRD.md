# SEO Article Writer - PRD

## Original Problem Statement
Aplikacja do pisania artykulow blogowych zwiazanych z ksiegowoscia, zoptymalizowana pod SEO AI.

## Tech Stack
- Backend: FastAPI + MongoDB (Motor async + PyMongo sync for threads)
- Frontend: React + Shadcn UI + Recharts
- AI: Gemini gemini-2.0-flash (primary) + OpenAI gpt-4.1-mini/gpt-5.2 (fallback) via Emergent LLM Key
- Image Generation: Gemini gemini-3.1-flash-image-preview (Nano Banana) via Emergent LLM Key

## Critical Architecture
- All LLM tasks use ThreadPoolExecutor + sync PyMongo + asyncio.new_event_loop()
- 3-model fallback chain: **gemini-2.0-flash -> gpt-4.1-mini -> gpt-5.2** with exponential backoff
- Image generation: **gemini-3.1-flash-image-preview** with 90s timeout per generation
- Shared LLM helper: `/app/backend/llm_helper.py` provides `llm_chat()` (async) and `llm_chat_sync()` (sync)
- Stale job recovery on startup + status checks
- Global Axios interceptor in App.js for automatic auth header injection

## Bug Fixes (2026-04-02)
- [x] P0: Image generation hanging - updated model from `gemini-3-pro-image-preview` to `gemini-3.1-flash-image-preview` 
- [x] P0: Image generation: fixed import from `FileContent` to `ImageContent`
- [x] P0: Image generation: added 90s timeout to prevent thread hanging forever
- [x] P0: Image generation: added stale job detection (120s) in status endpoint
- [x] P0: Article generation timeout too aggressive - increased from 180s to 360s

## All Completed Features (35+)
- [x] AI Article generation (E-E-A-T, legal refs, concrete data)
- [x] Visual editor + HTML view + formatting toolbar
- [x] Topic suggestions + AI Article Suggestions
- [x] AI SEO Assistant + Apply All
- [x] Image generator (Nano Banana gemini-3.1-flash-image-preview) + batch
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
- [x] Performance Dashboard (admin)
- [x] Plagiarism Checker + Content Verification / Fact-Check
- [x] Enhanced SEO Scorer (14 dimensions, E-E-A-T)
- [x] Auto Competition Analysis
- [x] A/B Title Testing
- [x] Bulk Article Operations
- [x] Auto Meta Tag Generation
- [x] Article Version History
- [x] Smart Publishing Schedule
- [x] Social Media Post Generator
- [x] SurferSEO Phase 1 & 2 (SERP, NLP, Keyword Research, URL Audit, Content Planner)
- [x] Social Media Scheduling
- [x] Email Notifications (MOCKED)
- [x] Competition Monitoring

## Backlog
- [ ] Refaktoryzacja server.py (~4300 linii) na oddzielne routery (P3)
- [ ] Integracja z prawdziwymi API platform social media (P3)
- [ ] Prawdziwe wysyłanie emaili (SendGrid/Resend) (P3)
