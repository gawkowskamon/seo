# SEO Article Writer - PRD

## Original Problem Statement
Aplikacja do pisania artykulow blogowych zwiazanych z ksiegowoscia, zoptymalizowana pod SEO AI.

## Tech Stack
- Backend: FastAPI + MongoDB (Motor async + PyMongo sync for threads)
- Frontend: React + Shadcn UI + Recharts
- AI: Gemini gemini-2.0-flash (primary) + OpenAI gpt-4.1-mini/gpt-5.2 (fallback) via Emergent LLM Key
- Image Generation: Gemini gemini-3.1-flash-image-preview (Nano Banana) via Emergent LLM Key

## Architecture (Refactored 2026-04-02)
```
/app/backend/
  server.py              # 115 lines - App creation, middleware, startup/shutdown
  routes/
    __init__.py
    api_routes.py        # ~4300 lines - All 117 API endpoints
  llm_helper.py          # Centralized LLM fallback logic
  surfer_seo_service.py  # SurferSEO engine
  article_generator.py   # Article generation with SurferSEO
  image_generator.py     # Image generation (Nano Banana)
  ... (other services)
```

## All Completed Features (35+)
- [x] AI Article generation + Visual editor + Templates
- [x] Topic suggestions + AI SEO Assistant + AI Chat + AI Rewriter
- [x] Image generator (Nano Banana) + batch + library
- [x] JWT auth, admin, multi-client workspaces
- [x] PDF/HTML/WordPress export
- [x] TPay subscription (mocked)
- [x] Content Calendar + Scheduled WordPress Publishing
- [x] Internal Link Building + Article Import
- [x] Dark Mode + Newsletter Generator
- [x] Keyword Analytics + Performance Dashboard
- [x] Plagiarism Checker + Content Verification
- [x] A/B Title Testing + Auto Meta Tags + Smart Schedule
- [x] Bulk Operations + Article Version History
- [x] Social Media Post Generator
- [x] SurferSEO (SERP, NLP, Keyword Research, URL Audit, Content Planner)
- [x] Social Media Scheduling
- [x] Email Notifications (MOCKED)
- [x] Competition Monitoring
- [x] server.py refactored: 4379 -> 115 lines (routes extracted to routes/api_routes.py)

## Backlog
- [ ] Further split routes/api_routes.py into smaller route modules (P3)
- [ ] Integracja z prawdziwymi API platform social media (P3)
- [ ] Prawdziwe wysyłanie emaili (SendGrid/Resend) (P3)
