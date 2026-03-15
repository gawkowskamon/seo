# SEO Article Writer - PRD

## Original Problem Statement
Aplikacja do pisania artykulow blogowych zwiazanych z ksiegowoscia, zoptymalizowana pod SEO AI.

## Tech Stack
- Backend: FastAPI + MongoDB (Motor async + PyMongo sync for threads)
- Frontend: React + Shadcn UI
- AI: OpenAI gpt-4.1-mini (text), gpt-5.2 (SEO assistant), Gemini nano-banana (images) via Emergent LLM Key

## Completed Features
- [x] Generowanie artykulow AI (async)
- [x] SEO AI Assistant (async polling)
- [x] Auto-optymalizacja SEO ("Zastosuj wszystkie")
- [x] Smart find-and-replace sugestii SEO (z walidacja HTML)
- [x] Generator obrazow Nano Banana (async polling)
- [x] Edytor wizualny z HTML sync
- [x] SEO scoring engine
- [x] Szablony tresci, Serie artykulow
- [x] JWT auth + admin role (env vars)
- [x] Eksport PDF/HTML/WordPress
- [x] WordPress import z autodiscovery REST API
- [x] Kalendarz tresci, Zaplanowane publikacje
- [x] Automatyczne linkowanie wewnetrzne
- [x] Import artykulow z URL
- [x] AI Chat, Dark Mode, Keyword Analytics, AI Rewriter, Newsletter
- [x] System subskrypcji TPay
- [x] Panel admina

## Async Pattern (ThreadPoolExecutor)
All LLM-calling endpoints now use async polling to avoid production proxy timeouts (30s):
- Article generation: POST /api/articles/generate -> GET /api/articles/generate/status/{job_id}
- SEO Assistant: POST /api/articles/{id}/seo-assistant -> GET /api/seo-assistant/status/{job_id}
- Image generation: POST /api/images/generate -> GET /api/images/generate/status/{job_id}
Root cause: emergentintegrations uses litellm.completion() (sync) inside async methods, blocking the event loop.
Solution: run_in_executor with sync PyMongo + asyncio.new_event_loop() in threads.

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
