# Kurdynowski SEO Article Builder - PRD

## Problem Statement
Feature-rich application for writing accounting-related blog articles with SEO optimization, AI-powered content generation, image generation, and a complete subscription system.

## Core Requirements
- Generate SEO-optimized articles with AI
- Visual WYSIWYG editor with formatting toolbar + HTML view
- AI SEO assistant for score improvement
- Image generator (Gemini Nano Banana) with reference images, styles, 4-variant batch, image library, lightbox, AI editing
- Direct image insertion into editor
- Content templates (standard, listicle, case study)
- Article series generation
- JWT authentication, multi-client workspaces, admin role
- Admin user management (CRUD) + app settings (WordPress config)
- PDF/HTML export matching editor styling ("1:1 export")
- WordPress integration (publish + companion plugin)
- Subscription system (monthly/semiannual/annual) with TPay payments

## Tech Stack
- **Backend**: FastAPI + MongoDB (Motor)
- **Frontend**: React + Shadcn/UI + styled-components
- **AI**: OpenAI gpt-4.1-mini/gpt-5.2 (text), Gemini nano-banana (images) via Emergent LLM Key
- **Payments**: TPay Open API (OAuth2 + transactions)
- **PDF**: fpdf2
- **HTTP Client**: httpx (backend)

## What's Implemented (All features complete)
- [x] JWT Authentication system
- [x] Admin role + User Management UI (CRUD)
- [x] Article generation + editing (visual editor + toolbar)
- [x] AI SEO assistant
- [x] Image generator (standalone page + editor component)
- [x] Reference image upload
- [x] Image library + lightbox viewer
- [x] Batch generation (4 variants)
- [x] AI image editing (inpainting, style transfer)
- [x] PDF export (with Polish font support - DejaVu)
- [x] HTML export
- [x] 1:1 branded export styling (Kurdynowski CSS)
- [x] WordPress integration (publish + plugin download)
- [x] Admin settings page (WordPress config)
- [x] Subscription system (3 plans: monthly/semiannual/annual)
- [x] TPay payment integration (FIXED: OAuth form-data, real credentials)
- [x] Pricing page with checkout flow
- [x] Content templates
- [x] Article series generation
- [x] Topic suggestions

## Key Credentials
- Admin: monika.gawkowska@kurdynowski.pl / MonZuz8180!
- TPay: Configured in backend/.env (TPAY_CLIENT_ID, TPAY_CLIENT_SECRET)

## Architecture
```
/app/backend/
  server.py          - Main FastAPI app (all endpoints)
  auth.py            - JWT auth module
  tpay_service.py    - TPay OAuth + transaction creation
  export_service.py  - PDF/HTML export
  wordpress_service.py - WP publishing + plugin
  article_generator.py
  image_generator.py
  seo_assistant.py / seo_scorer.py
  content_templates.py / series_generator.py

/app/frontend/src/
  pages/             - All page components
  components/        - Reusable components (editor, sidebar, etc.)
  contexts/          - AuthContext
```

## Subscription Plans
| Plan | Netto | Brutto (VAT 23%) | Discount |
|------|-------|-------------------|----------|
| Miesięczny | 59.99 PLN | 73.79 PLN | 0% |
| Półroczny | 334.74 PLN | 411.74 PLN | 7% |
| Roczny | 611.90 PLN | 752.63 PLN | 15% |

## Status: All features complete and tested
- Last test: iteration_12.json - 100% pass rate (backend + frontend)
- TPay: Real credentials, real transactions created on tpay.com
