# SEO Article Writer - PRD

## Original Problem Statement
Aplikacja do pisania artykulow blogowych zwiazanych z ksiegowoscia, zoptymalizowana pod SEO AI.

## Tech Stack
- Backend: FastAPI + MongoDB (Motor async + PyMongo sync for threads)
- Frontend: React + Shadcn UI + Recharts
- AI Text: Gemini gemini-2.0-flash (primary) + OpenAI gpt-4.1-mini/gpt-5.2 (fallback)
- AI Images: Gemini gemini-3.1-flash-image-preview (Nano Banana)
- All via Emergent LLM Key

## Architecture (Refactored 2026-04-02)
```
/app/backend/
  server.py              # 126 lines - App, middleware, startup/shutdown
  shared.py              # 260 lines - DB, auth, Pydantic models
  routes/
    auth.py              # 9 routes - Auth & Admin
    articles.py          # 13 routes - CRUD, generation, export
    surfer.py            # 8 routes - SurferSEO
    images.py            # 11 routes - Image gen & library
    content.py           # 19 routes - WordPress, calendar, chat
    seo_tools.py         # 32 routes - SEO audit, analytics, plagiarism
    ai_features.py       # 12 routes - Bulk, versions, meta, schedule
    social.py            # 4 routes - Social scheduling
    notifications.py     # 5 routes - Email notifications
    competition_monitor.py # 4 routes - Competition monitoring
  ──── Total: 117 API endpoints ────
  llm_helper.py, surfer_seo_service.py, article_generator.py,
  image_generator.py, seo_scorer.py, ... (services)
```

## Bug Fixes (2026-04-02)
- [x] Image gen hanging: model -> gemini-3.1-flash-image-preview + 90s timeout + stale detection
- [x] Article gen timeout: 180s -> 360s
- [x] Import fix: FileContent -> ImageContent for image references
- [x] Shared ThreadPoolExecutor for all background jobs

## All Features (35+)
- [x] AI Article generation + Visual editor + Templates
- [x] Topic suggestions + AI SEO Assistant + AI Chat + AI Rewriter
- [x] Image generator (Nano Banana) + batch + library
- [x] JWT auth, admin, multi-client workspaces
- [x] PDF/HTML/WordPress export
- [x] TPay subscription (mocked), Content Calendar, Scheduled Publishing
- [x] Internal Link Building + Article Import
- [x] Dark Mode + Newsletter Generator + Keyword Analytics + Performance Dashboard
- [x] Plagiarism Checker + Content Verification
- [x] A/B Title Testing + Auto Meta Tags + Smart Schedule
- [x] Bulk Operations + Article Version History
- [x] Social Media Post Generator + Scheduling
- [x] SurferSEO (SERP, NLP, Keyword Research, URL Audit, Content Planner)
- [x] Email Notifications (MOCKED) + Competition Monitoring
- [x] server.py refactored into 10 route modules (117 endpoints)

## Testing: iteration_31 - 100% (38/38 backend, 100% frontend)

## Backlog
- [ ] Prawdziwe wysyłanie emaili (SendGrid/Resend) (P3)
- [ ] Integracja z prawdziwymi API social media (P3)
