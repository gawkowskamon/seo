# SEO Article Writer - PRD

## Original Problem Statement
Aplikacja do pisania artykulow blogowych zwiazanych z ksiegowoscia, zoptymalizowana pod SEO AI.

## Tech Stack
- Backend: FastAPI + MongoDB (Motor async + PyMongo sync for threads)
- Frontend: React + Shadcn UI
- AI: OpenAI gpt-4.1-mini, gpt-5.2, Gemini nano-banana via Emergent LLM Key

## Critical Architecture: ThreadPoolExecutor for ALL LLM calls
Root cause: emergentintegrations uses litellm.completion() (SYNC) inside async methods.
This blocks the FastAPI event loop, preventing status polling and causing proxy timeouts.
Solution: ALL LLM-calling background tasks use run_in_executor + sync PyMongo + asyncio.new_event_loop()

Migrated endpoints:
- Article generation: _sync_run_generation_job
- SEO Assistant: _sync_seo_assistant
- Image generation: _sync_generate_image
- Batch image generation: _sync_generate_batch
- SEO Audit: _sync_run_seo_audit
- Competition analysis: _sync_run_competition
- Keyword analytics: _sync_run_keyword_analytics
- AI Rewriter: _sync_run_rewrite
- AI Article Suggestions: _sync_run_ai_suggestions
- Plagiarism Checker: _sync_run_plagiarism_check

Stale job timeout increased from 3min to 5min to accommodate thread pool execution.

## Credentials
- Admin: ADMIN_EMAIL / ADMIN_PASSWORD (z .env)
- WordPress: monika.gawkowska@kurdynowski.pl / jY67 vfXG WSqw Wic4 LRRg CJUw
- WordPress URL: https://kurdynowski.com.pl/cms-biuro

## Completed Features
- [x] Article generation with AI (GPT)
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
- [x] AI Article Suggestions (NEW - 2026-03-23)
- [x] Performance Dashboard (NEW - 2026-03-23)
- [x] Plagiarism Checker (NEW - 2026-03-23)

## Backlog (P2+)
- [ ] A/B Testing tytulow
- [ ] Integracja Social Media
- [ ] Masowe operacje na artykulach
- [ ] Historia wersji artykulow
- [ ] Auto generowanie meta tagow
- [ ] WordPress export stylizacja (identyczna jak edytor)
