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
- [x] Article generation + visual WYSIWYG editor
- [x] AI SEO assistant + scoring
- [x] Content templates (standard, listicle, case study)
- [x] Article series generation
- [x] Topic suggestions

### Image Features
- [x] Image generator (Nano Banana) with 7 styles
- [x] **Multiple reference images (up to 5)** - NEW
- [x] Batch generation (4 variants)
- [x] Image library + lightbox viewer
- [x] AI image editing (inpainting, style transfer)

### Export & Publishing
- [x] PDF export (Polish font DejaVu)
- [x] HTML export
- [x] 1:1 branded Kurdynowski CSS in exports
- [x] WordPress integration (publish + plugin)
- [x] **Scheduled publishing** (date/time picker in editor) - NEW

### SEO Intelligence (Phase 2)
- [x] **SEO Audit** - scrape any URL + AI recommendations - NEW
- [x] **Competition Analysis** - compare your article vs competitor - NEW
- [x] **Auto-Update Check** - AI monitors tax/legal changes - NEW
- [x] **Internal Linkbuilding** - AI suggests links between articles - NEW

### Content Management (Phase 1)
- [x] **Content Calendar** - AI-generated publishing plan per tax season - NEW
- [x] **Import Articles** - from URL or WordPress REST API - NEW

### Payments & Branding
- [x] Subscription system (monthly/semi-annual/annual)
- [x] TPay payment integration (real credentials)
- [x] **Professional generated logo** - NEW
- [x] **Modernized premium design** - NEW

## Key Credentials
- Admin: monika.gawkowska@kurdynowski.pl / MonZuz8180!
- TPay: Configured in backend/.env

## Upcoming (Phase 3)
- [ ] Social media integration (Facebook/LinkedIn post generation)

## Architecture
```
/app/backend/
  server.py              # Main FastAPI (all endpoints)
  auth.py                # JWT auth
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
  components/            # Reusable (Sidebar, ImageGenerator, etc.)
  contexts/              # AuthContext
```

## Test Reports
- iteration_12.json: TPay fix - 100% pass
- iteration_13.json: Phase 1 features - 100% pass
- iteration_14.json: Phase 2 + Design - 100% pass
