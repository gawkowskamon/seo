# Kurdynowski SEO Article Builder - PRD

## Problem Statement
Feature-rich application for writing accounting-related blog articles with SEO optimization, AI-powered content generation, image generation, and a complete subscription system.

## Tech Stack
- **Backend**: FastAPI + MongoDB (Motor)
- **Frontend**: React + Shadcn/UI
- **AI**: OpenAI gpt-4.1-mini via Emergent LLM Key, Gemini nano-banana (images)
- **Payments**: TPay Open API (OAuth2, MOCKED credentials)
- **PDF**: fpdf2

## What's Implemented

### Core Features
- [x] JWT Authentication + Admin role + auto-seeding
- [x] Admin user management (CRUD)
- [x] Article generation (async background jobs) + visual WYSIWYG editor
- [x] AI SEO assistant + flexible keyword scoring
- [x] Content templates (standard, listicle, case study)
- [x] Article series generation
- [x] Topic suggestions

### Image Features
- [x] Image generator (Nano Banana) with 7 styles
- [x] **Multiple reference images** (up to 5) — all attachments sent to Gemini for analysis
- [x] Batch generation (4 variants)
- [x] Image library + lightbox viewer
- [x] AI image editing

### Export & Publishing
- [x] PDF/HTML export with branded styling
- [x] WordPress integration with scheduled publishing
- [x] **Styled WordPress Export** - Inline CSS styles matching in-app editor (fonts, colors, spacing, separators, TOC, FAQ, tables)

### SEO Intelligence
- [x] SEO Audit - async background job
- [x] Competition Analysis - async background job
- [x] Auto-Update Check
- [x] Internal Linkbuilding

### Content Management
- [x] Content Calendar
- [x] Import Articles from URL/WordPress

### "Wow" Effects (ALL COMPLETE)
- [x] **Dark Mode** - toggle in sidebar, localStorage persistence
- [x] **AI Chat Assistant** - Chat tab in article editor
- [x] **Keyword Analytics Dashboard** - trends, difficulty, CPC, opportunity scores, mini-charts
- [x] **AI Rewriter** - 6 styles (profesjonalny, przystępny, ekspercki, SEO, skrócony, rozszerzony) in editor
- [x] **Newsletter Generator** - auto-generate HTML newsletters from articles, 3 styles, copy/download
- [x] **Flexible SEO Scoring** - intelligent keyword matching ignoring Polish stop words

### Payments & Branding
- [x] Subscription system (TPay MOCKED)
- [x] Professional logo + modernized UI

## Key Credentials
- Admin: monika.gawkowska@kurdynowski.pl / MonZuz8180!

## API Endpoints (New)
- `POST /api/keyword-analytics/analyze` → `GET /api/keyword-analytics/status/{job_id}`
- `POST /api/rewrite` → `GET /api/rewrite/status/{job_id}`
- `POST /api/newsletter/generate`, `GET /api/newsletter/list`, `GET /api/newsletter/{id}`

## Test Reports
- iteration_15.json: Dark Mode, AI Chat, Async SEO - 100% pass
- iteration_16.json: Keyword Analytics, Newsletter, AI Rewriter - 100% pass
- iteration_17.json: WordPress Styled Export - 14/14 pass (100%)
- iteration_18.json: Multiple Reference Images - 100% pass (backend + frontend)
- iteration_19.json: Article Generation Fix (MongoDB jobs) - 100% pass

## Backlog
- [ ] Social media integration (Facebook/LinkedIn post generation)
- [ ] Masowe operacje na artykułach
- [ ] Auto meta tags generation
- [ ] Historia wersji artykułów
