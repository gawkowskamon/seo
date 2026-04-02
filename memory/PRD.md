# SEO Article Writer - Kurdynowski

## Problem Statement
Feature-rich application for writing and managing accounting-related blog articles with SEO optimization, WordPress integration, and AI-powered content tools.

## Stack
FARM (FastAPI, React, MongoDB) with Emergent LLM Key for AI (Gemini + OpenAI)

## Core Features (Implemented)
- Article generation with AI (async, background jobs)
- Visual editor with formatting toolbar + HTML view
- SurferSEO scoring panel (SERP analysis, keyword metrics, NLP terms)
- **Auto-optimize based on SurferSEO** — AI automatically applies recommendations
- AI suggestions for topics
- Meta regeneration (meta title/description, FAQ)
- Image generation (gemini-3.1-flash-image-preview) — single + batch (4 variants)
- PDF/HTML/WordPress export with styled inline CSS
- **SEO Report PDF export** — downloadable PDF with SERP preview, metrics, readiness checklist
- WordPress REST API publishing + WordPress Plugin generator
- WordPress Preview panel in Article Editor with SEO comparison
- JWT auth, admin role, auto-seeded admin account
- Content Calendar with scheduled WordPress publishing
- AI Chat Assistant, AI Rewriter, Newsletter Generator
- Dark Mode toggle
- Keyword Analytics Dashboard
- Article import from URL + WordPress import
- Internal link building

## SurferSEO Features (Implemented)
- Keyword Research (standalone page)
- Content Planner (cluster analysis)
- URL Audit (standalone page)
- SERP Analysis (async with polling)
- Score computation (9 metrics)
- **Auto-optimize with AI** (async, applies all recommendations)

## Additional Features (Implemented)
- Social Media Scheduling
- Email Notifications system
- Competition Monitor
- Subscription system (TPay - MOCKED)

## Backend Architecture
```
/app/backend/
  server.py          # App init, router inclusion (~130 lines)
  shared.py          # DB, auth, Pydantic models
  routes/
    ai_features.py   # AI suggestions, auto-meta, auto-links
    articles.py      # CRUD, generation, export, regeneration
    auth.py          # Login, register, user management
    competition_monitor.py
    content.py       # WordPress settings, publishing, rewrite, newsletter
    images.py        # Image generation (single + batch)
    notifications.py
    seo_tools.py     # SEO audit, keyword analytics
    social.py        # Social media scheduling
    surfer.py        # SurferSEO endpoints + PDF report + auto-optimize
```

## Key Credentials
- Admin: monika.gawkowska@kurdynowski.pl / MonZuz8180!

## Current Status (April 2, 2026)
- All features functional
- SEO Report PDF export working
- Auto-optimize with AI working (async, ~45s processing)
- Image generation fixed
- WordPress Preview with SEO comparison
- Test iterations 32-34: All passing

## Backlog
- [ ] A/B Testing for titles (P2)
- [ ] Real email sending via SendGrid/Resend (P3)
- [ ] Real social media API integration (P3)
