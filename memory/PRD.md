# SEO Article Writer - Kurdynowski

## Problem Statement
Feature-rich application for writing and managing accounting-related blog articles with SEO optimization, WordPress integration, and AI-powered content tools.

## Stack
FARM (FastAPI, React, MongoDB) with Emergent LLM Key for AI (Gemini + OpenAI)

## Core Features (Implemented)
- Article generation with AI (async, background jobs)
- Visual editor with formatting toolbar + HTML view
- SurferSEO scoring panel (SERP analysis, keyword metrics, NLP terms)
- **Auto-optimize with AI** — multi-step approach (plan → sections → FAQ)
- Basic SEO scoring (keyword density, meta, headings, content length)
- AI suggestions for topics
- Meta regeneration (meta title/description, FAQ)
- Image generation (gemini-3.1-flash-image-preview) — single + batch
- PDF/HTML/WordPress export with styled inline CSS
- **SEO Report PDF export** — downloadable PDF with all SEO metrics
- WordPress REST API publishing + WordPress Plugin generator
- WordPress Preview panel with SEO comparison (SERP preview, readiness checklist)
- JWT auth, admin role, auto-seeded admin account
- Content Calendar with scheduled WordPress publishing
- AI Chat Assistant, AI Rewriter, Newsletter Generator
- Dark Mode toggle
- Keyword Analytics Dashboard
- Article import from URL + WordPress import
- Internal link building

## SurferSEO Features (Implemented)
- Keyword Research, Content Planner, URL Audit (standalone pages)
- SERP Analysis (async with polling)
- Score computation (9 metrics)
- **Auto-optimize** — AI applies all recommendations automatically

## Additional Features (Implemented)
- Social Media Scheduling, Email Notifications, Competition Monitor
- Subscription system (TPay - MOCKED)

## Key Credentials
- Admin: monika.gawkowska@kurdynowski.pl / MonZuz8180!

## Current Status (April 2, 2026)
- All features functional, all bugs resolved
- Test iterations 32-35: All passing (100%)

## Backlog
- [ ] A/B Testing for titles (P2)
- [ ] Real email sending via SendGrid/Resend (P3)
- [ ] Real social media API integration (P3)
