# SEO Article Writer – Polish Accounting Blog Platform

## Original Problem Statement
Aplikacja do pisania artykułów blogowych związanych z księgowością, zoptymalizowana pod SEO AI. Wymagania: generowanie artykułów z wysokim scoringiem SEO, wizualny edytor, wielu klientów, JWT auth, integracja WordPress, eksport PDF/HTML, system subskrypcji (TPay), integracja SurferSEO, social media, email, monitoring konkurencji.

## User Persona
Monika (admin) – Kurdynowski Accounting & Tax Solutions. Używa aplikacji do tworzenia artykułów SEO po polsku o księgowości/podatkach dla klientów biura.

## Tech Stack
- **Backend:** FastAPI, Python, MongoDB (async Motor + sync pymongo for threads)
- **Frontend:** React 19, Tailwind, shadcn/ui, lucide-react icons
- **AI:** Emergent LLM Key (gemini-2.0-flash, gemini-3.1-flash-image, gpt fallback)
- **Libs:** fpdf2 (PDF), trafilatura (scraping), emergentintegrations

## Current Status (April 17, 2026)
**All core features functional and tested (iteration 36: 16/16 passed 100%)**

### Completed in this session
- [x] **FIX (2026-04-17 12:15):** Optimize-loop "Do 80%+" i 1x Optymalizuj crash `NoneType` — wszystkie ścieżki wrażliwe na None (section content, html_content, heading) zabezpieczone wzorcem `x.get("content") or ""` w: surfer_seo_service.py, seo_scorer.py, surfer.py (_apply_to_db, _run_optimize, _run_loop), export_service.py, wordpress_service.py, routes/ai_features.py, routes/seo_tools.py
- [x] **FIX:** SurferSEO auto-optimize & loop: naprawione prompty generujące placeholder ("200+ slow")
- [x] **FIX:** Galeria obrazów w edytorze — zwraca pole `data` dla miniatur
- [x] **FIX:** Timeout polling generatora 3→6 min
- [x] **FIX:** `onArticleUpdate` + `onRestore` odświeżają htmlContent + meta fields
- [x] **Content Versioning UI** — historia wersji z tagami źródła (ręczna/auto-optimize/loop/pre-restore), miniatura SEO score, przywracanie
- [x] **Multi-language generation** — PL/EN/DE/UK (selector w generatorze, system prompts per-język)
- [x] **ROI Dashboard** — nowa strona `/roi` z:
  - Sumaryczne statystyki (total, avg SEO, publish rate, total words)
  - Rozkład jakości SEO (excellent/good/medium/poor buckets)
  - Status articles (published/scheduled/draft)
  - Rozkład językowy
  - Trend publikacji 6 miesięcy (bar chart)
  - Top 5 performers i Bottom 5 (z linkami do edytora)

### Previously completed
- [x] Article generation (Gemini 2.0 Flash + GPT fallback, multi-step)
- [x] SurferSEO SERP analysis + iterative optimization to 80%+
- [x] Image generation (Gemini Nano Banana)
- [x] WordPress Preview with SEO comparison
- [x] A/B Title testing (ABTitleTestPanel + backend)
- [x] Smart Schedule suggestions (SmartSchedulePanel)
- [x] PDF SEO report export (fpdf2)
- [x] 8 article templates (standard, poradnik, case study, porównanie, checklist, pillar, aktualizacja, kalkulator)
- [x] WordPress publish integration
- [x] Plagiarism checker
- [x] URL audit
- [x] Keyword research
- [x] Admin panel, user management, workspaces
- [x] Notifications
- [x] Competition monitoring
- [x] TPay subscription (MOCKED credentials)

## Data Model
- `articles`: id, user_id, workspace_id, title, html_content, sections[], faq[], sources[], toc[], meta_title, meta_description, surfer_data, surfer_score, seo_score, status, language, created_at, published_at
- `article_versions`: id, article_id, user_id, version_data, **source** (manual_edit|auto_optimize|optimize_loop|pre_restore), created_at
- `images`: id, article_id, user_id, prompt, style, mime_type, data (base64), variant_of, created_at
- `generation_jobs`, `image_generation_jobs`: temp status tracking
- `_optimize_jobs`, `_optimize_loops`: in-memory loop tracking

## Key API Endpoints
- `POST /api/articles/generate` (supports `language` param)
- `GET /api/articles/{id}/versions` (includes source)
- `POST /api/articles/{id}/versions/{vid}/restore`
- `POST /api/surfer/auto-optimize/{id}` (1x)
- `POST /api/surfer/optimize-loop/{id}` (Do 80%+)
- `POST /api/articles/{id}/seo-report/pdf`
- `GET /api/stats/roi` (NEW - ROI dashboard data)
- `GET /api/articles/{id}/images` (NOW includes base64 data)

## Backlog (P0/P1/P2)
### P0 (next)
- [ ] Auto-publish & Client Reporting — planowana publikacja do WordPress z auto-raportem tygodniowym/miesięcznym dla klientów (PDF z top artykułami, avg score, trend)

### P1 (next-next)
- [ ] ROI Dashboard extension — Google Analytics/Search Console integration (wymaga OAuth)
- [ ] Real email sending via SendGrid/Resend
- [ ] Real social media API integration (LinkedIn/Facebook/Twitter)

### P2 (future)
- [ ] Team collaboration — wielu użytkowników edytuje ten sam artykuł
- [ ] Automatyczna rotacja A/B test wyników (obecnie tylko generuje warianty)
- [ ] Content calendar view z drag-drop

## Critical Info for New Agent
- **Auth tokens:** always use `auth_token` key in localStorage (NOT `token`)
- **Async vs Sync in threads:** background workers using `threading.Thread` MUST use sync `pymongo.MongoClient`, not async Motor `shared.db`
- **LLM JSON truncation:** break large gens into multi-step (plan→body→FAQ). Use `_try_parse_json` repair helper
- **LLM prompts: NEVER use placeholder content strings like "200+ slow" or "Treść 150-250 słów"** — LLM copies them verbatim. Always specify explicit requirements ("Pełna merytoryczna treść 200-300 słów...")
- **MongoDB responses:** exclude `_id` always. For articles, include `data` in images for thumbnails
- **Version sources:** tag every `article_versions` insert with `source` field
- **Languages supported:** `pl` (default Polish accounting), `en`, `de`, `uk`
