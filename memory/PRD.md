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

Stale job timeout increased from 3min to 5min to accommodate thread pool execution.

## Credentials
- Admin: ADMIN_EMAIL / ADMIN_PASSWORD (z .env)
- WordPress: monika.gawkowska@kurdynowski.pl / jY67 vfXG WSqw Wic4 LRRg CJUw
- WordPress URL: https://kurdynowski.com.pl/cms-biuro

## Backlog (P2+)
- [ ] A/B Testing tytulow
- [ ] Integracja Social Media
- [ ] Masowe operacje na artykulach
- [ ] Historia wersji artykulow
- [ ] Auto generowanie meta tagow
