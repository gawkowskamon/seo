# Kurdynowski SEO Article Builder - PRD

## Problem Statement
Feature-rich application for writing accounting-related blog articles with SEO optimization, AI-powered content generation, image generation, and a complete subscription system.

## Tech Stack
- **Backend**: FastAPI + MongoDB (Motor)
- **Frontend**: React + Shadcn/UI + styled-components
- **AI**: OpenAI gpt-4.1-mini/gpt-5.2 via Emergent LLM Key, Gemini nano-banana (images)
- **Payments**: TPay Open API (OAuth2)
- **PDF**: fpdf2

## What's Implemented

### Core Features
- [x] JWT Authentication + Admin role
- [x] Admin user management (CRUD)
- [x] Article generation (async background jobs) + visual WYSIWYG editor
- [x] AI SEO assistant + scoring
- [x] Content templates (standard, listicle, case study)
- [x] Article series generation
- [x] Topic suggestions

### Image Features
- [x] Image generator (Nano Banana) with 7 styles
- [x] Multiple reference images (up to 5)
- [x] Batch generation (4 variants)
- [x] Image library + lightbox viewer
- [x] AI image editing (inpainting, style transfer)

### Export & Publishing
- [x] PDF export (Polish font DejaVu)
- [x] HTML export
- [x] 1:1 branded Kurdynowski CSS in exports
- [x] WordPress integration (publish + plugin)
- [x] Scheduled publishing (date/time picker in editor)

### SEO Intelligence (Phase 2)
- [x] SEO Audit - async scrape any URL + AI recommendations
- [x] Competition Analysis - async compare article vs competitor
- [x] Auto-Update Check - AI monitors tax/legal changes
- [x] Internal Linkbuilding - AI suggests links between articles

### Content Management (Phase 1)
- [x] Content Calendar - AI-generated publishing plan per tax season
- [x] Import Articles - from URL or WordPress REST API

### "Wow" Effects
- [x] **Dark Mode** - toggle in sidebar, persists in localStorage, full CSS variable theming
- [x] **AI Chat Assistant** - contextual AI chat in article editor (Chat tab in right panel)
- [x] **Async SEO Audit** - no more timeouts, background job + polling pattern
- [x] **Async Competition Analysis** - background job + polling pattern

### Payments & Branding
- [x] Subscription system (monthly/semi-annual/annual)
- [x] TPay payment integration (MOCKED credentials)
- [x] Professional generated logo
- [x] Modernized premium design with dark/light themes

## Key Credentials
- Admin: monika.gawkowska@kurdynowski.pl / MonZuz8180!
- TPay: Configured in backend/.env (mocked)

## Upcoming Tasks
- [ ] Keyword Analytics Dashboard - charts & trend data for keywords (P1)

## Future/Backlog
- [ ] Social media integration (Facebook/LinkedIn post generation)

## Architecture
```
/app/backend/
  server.py              # Main FastAPI (all endpoints, async jobs)
  auth.py                # JWT auth
  chat_assistant_service.py # AI chat assistant
  tpay_service.py        # TPay OAuth + transactions
  seo_audit_service.py   # URL scraping + AI audit
  competition_service.py # Competitor analysis
  auto_update_service.py # Legal change monitoring
  content_calendar_service.py # AI content planning
  import_service.py      # URL/WordPress article import
  linkbuilding_service.py # Internal link suggestions
  export_service.py      # PDF/HTML export
  wordpress_service.py   # WP publishing + plugin

/app/frontend/src/
  pages/                 # 14 page components
  components/            # Reusable (Sidebar, AIChatPanel, ImageGenerator, etc.)
  contexts/              # AuthContext
```

## Test Reports
- iteration_12.json: TPay fix - 100% pass
- iteration_13.json: Phase 1 features - 100% pass
- iteration_14.json: Phase 2 + Design - 100% pass
- iteration_15.json: Wow Effects (Dark Mode, AI Chat, Async SEO) - 100% pass

## Project Health
- **Working**: All features, dark mode, AI chat, async SEO audit, async competition analysis
- **Mocked**: TPay payment credentials
