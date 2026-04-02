# SEO Article Writer - PRD

## Original Problem Statement
Aplikacja do pisania artykulow blogowych zwiazanych z ksiegowoscia, zoptymalizowana pod SEO AI.

## Tech Stack
- Backend: FastAPI + MongoDB (Motor async + PyMongo sync for threads)
- Frontend: React + Shadcn UI + Recharts
- AI: Gemini gemini-2.0-flash (primary) + OpenAI gpt-4.1-mini/gpt-5.2 (fallback) via Emergent LLM Key
- Scraping: httpx + BeautifulSoup (DuckDuckGo)

## Critical Architecture
- All LLM tasks use ThreadPoolExecutor + sync PyMongo + asyncio.new_event_loop()
- 3-model fallback chain: **gemini-2.0-flash -> gpt-4.1-mini -> gpt-5.2** with exponential backoff
- Shared LLM helper: `/app/backend/llm_helper.py` provides `llm_chat()` (async) and `llm_chat_sync()` (sync)
- Stale job recovery on startup: auto-marks stuck "generating" jobs as failed
- Gemini is PRIMARY model because OpenAI frequently returns 502 Bad Gateway
- Global Axios interceptor in App.js for automatic auth header injection

## Credentials
- Admin: ADMIN_EMAIL / ADMIN_PASSWORD (z .env)
- WordPress: monika.gawkowska@kurdynowski.pl / jY67 vfXG WSqw Wic4 LRRg CJUw

## All Completed Features (35+)
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
- [x] Social Media Post Generator (LinkedIn/Twitter/Facebook/Instagram x 3 tones)
- [x] SurferSEO Phase 1: SERP analysis, NLP terms, content scoring in editor
- [x] SurferSEO Phase 2: Keyword Research, Content Planner, URL Audit
- [x] Social Media Scheduling - plan, manage, publish posts
- [x] Email Notifications - article update alerts (MOCKED email)
- [x] Competition Monitoring - AI-powered SERP tracking with content gaps

## Features Added (2026-04-02)

### SurferSEO Phase 2
- Keyword Research page (/keyword-research) - seed keyword -> 15-25 related keywords
- Content Planner (via "Klastruj" button) - keyword clustering into article topics
- URL Audit page (/audyt-url) - full SEO audit of any URL

### Social Media Scheduling
- Schedule posts for LinkedIn/Twitter/Facebook/Instagram
- View/manage scheduled and published posts
- Copy text, mark as published, delete
- Pages: /social-media

### Email Notifications
- Notification preferences (email toggle, frequency, alert types)
- Check article updates (age alerts, low SEO score alerts)
- Test email sending (MOCKED)
- Email history log
- Pages: /powiadomienia

### Competition Monitoring
- Add keywords to monitor with AI-powered SERP analysis
- View TOP results, content gaps, recommendations
- Refresh analysis, delete monitors
- Direct link to create article from monitored keyword
- Pages: /konkurencja

## Key API Endpoints
### SurferSEO
- POST /api/surfer/analyze-serp, /api/surfer/analyze-serp/async
- GET /api/surfer/analyze-serp/status/{job_id}
- POST /api/surfer/score, /api/surfer/keyword-research
- POST /api/surfer/content-planner, /api/surfer/audit-url

### Social Media
- POST /api/social/schedule
- GET /api/social/scheduled
- DELETE /api/social/scheduled/{id}
- PUT /api/social/scheduled/{id}/publish

### Notifications
- GET/PUT /api/notifications/settings
- POST /api/notifications/check-updates
- POST /api/notifications/send-test
- GET /api/notifications/history

### Competition
- POST /api/competition/monitor
- GET /api/competition/monitors
- DELETE /api/competition/monitors/{id}
- POST /api/competition/monitors/{id}/refresh

## DB Collections
- articles, users, generation_jobs, seo_jobs
- scheduled_posts (Social Media)
- notification_settings, notification_log (Notifications)
- competition_monitors (Competition)

## Backlog
- [ ] Refaktoryzacja server.py (~4300 linii) na oddzielne routery (P3)
- [ ] Integracja z prawdziwymi API platform social media (wymaga kluczy OAuth) (P3)
- [ ] Prawdziwe wysyłanie emaili (SendGrid/Resend) (P3)
