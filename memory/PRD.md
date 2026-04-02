# SEO Article Writer - Kurdynowski

## Problem Statement
Feature-rich application for writing and managing accounting-related blog articles with SEO optimization, WordPress integration, and AI-powered content tools.

## Stack
FARM (FastAPI, React, MongoDB) with Emergent LLM Key for AI (Gemini + OpenAI)

## Core Features (Implemented)
- Article generation with AI (async, background jobs)
- Visual editor with formatting toolbar + HTML view
- SurferSEO scoring panel (SERP analysis, keyword metrics, NLP terms)
- **Iterative auto-optimize** (AI loop targeting 80%+ SurferSEO score)
- Single-step auto-optimize (one iteration)
- Basic SEO scoring, AI topic suggestions, Meta regeneration
- Image generation (gemini-3.1-flash-image-preview) — single + batch
- PDF/HTML/WordPress export with styled inline CSS
- SEO Report PDF export
- WordPress Preview panel with SEO comparison
- JWT auth, admin role, Content Calendar, AI Chat, AI Rewriter, Newsletter
- Dark Mode, Keyword Analytics, Article import, Internal linking
- Social Media Scheduling, Notifications, Competition Monitor
- Subscription system (TPay - MOCKED)

## Key Technical Notes
- Auth token: `auth_token` in localStorage (AuthContext.js)
- Iterative optimize uses synchronous pymongo in background thread (avoids Motor event loop issues)
- Visual editor managed via editorContentRef (not state)

## Key Credentials
- Admin: monika.gawkowska@kurdynowski.pl / MonZuz8180!

## Current Status (April 2, 2026)
- All features functional
- Iterative optimization: 55% → 85% in one iteration (target 80%+)
- Test iterations 32-35 all passing

## Backlog
- [ ] A/B Testing for titles (P2)
- [ ] Real email sending via SendGrid/Resend (P3)
- [ ] Real social media API integration (P3)
